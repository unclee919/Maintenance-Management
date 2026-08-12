import frappe
from frappe.utils import flt, now

@frappe.whitelist()
def update_technician_location(sales_order, latitude=None, longitude=None, tracking_status="active"):
    """Updates technician GPS location, handles automatic check-in based on geofencing, and handles GPS failover."""
    try:
        so = frappe.get_doc("Sales Order", sales_order)
        tech_name = so.get("custom_assigned_technician")
        if not tech_name:
            # Fallback to any active technician if none assigned on SO
            techs = frappe.get_all("Field Technician", limit=1)
            if techs:
                tech_name = techs[0].name
            else:
                return {"status": "error", "message": "No technician found"}

        tech = frappe.get_doc("Field Technician", tech_name)
        settings = frappe.get_single("Field Maintenance Settings")
        
        # GPS Failover Handling: If latitude or longitude are missing/None, keep last known coordinates and log warning
        if latitude is None or longitude is None or tracking_status == "interrupted":
            frappe.logger().warning(f"GPS Signal Interrupted for Technician {tech_name}. Retaining last known position: Lat={tech.get('current_latitude')}, Lon={tech.get('current_longitude')}")
            tech.db_set("status", "GPS Interrupted")
            if sales_order:
                so.append("custom_location_audit_logs", {
                    "technician": tech_name,
                    "action_name": "GPS Signal Interrupted - Failover Active",
                    "latitude": tech.get("current_latitude") or 0.0,
                    "longitude": tech.get("current_longitude") or 0.0,
                    "timestamp": now()
                })
                so.save(ignore_permissions=True)
                frappe.db.commit()
            return {
                "status": "success",
                "message": "GPS signal interrupted. Failover mode active: last known position retained.",
                "failover": True,
                "last_latitude": tech.get("current_latitude"),
                "last_longitude": tech.get("current_longitude")
            }

        lat = flt(latitude)
        lon = flt(longitude)
        
        tech.current_latitude = lat
        tech.current_longitude = lon
        tech.last_location_update = now()
        
        # Check Auto-Check-in Office Geofence
        off_lat = flt(settings.get("company_office_latitude") or 30.0444)
        off_lon = flt(settings.get("company_office_longitude") or 31.2357)
        off_radius = flt(settings.get("company_office_radius_km") or 1.0)
        
        import math
        def calc_dist(lat1, lon1, lat2, lon2):
            R = 6371.0
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
            c = 2 * math.asin(math.sqrt(a))
            return R * c
            
        dist_office = calc_dist(lat, lon, off_lat, off_lon)
        if dist_office <= off_radius:
            tech.status = "Available (Auto Checked-In)"
        else:
            tech.status = "On Field / Active"
            
        tech.save(ignore_permissions=True)
        
        if sales_order:
            so.append("custom_location_audit_logs", {
                "technician": tech_name,
                "action_name": "Location Updated (Geofence Active)",
                "latitude": lat,
                "longitude": lon,
                "timestamp": now()
            })
            so.save(ignore_permissions=True)
            
        frappe.db.commit()
        return {
            "status": "success",
            "technician": tech_name,
            "distance_to_office_km": round(dist_office, 2),
            "auto_checked_in": dist_office <= off_radius,
            "technician_status": tech.status
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "GPS Failover Location Update Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def transfer_technician_cash(technician, amount, reference_note=None):
    """Transfers cash collections from technician to the main company treasury via Journal Entry."""
    try:
        amt = flt(amount)
        if amt <= 0:
            return {"status": "error", "message": "Invalid transfer amount"}
            
        company = frappe.defaults.get_defaults().get("company")
        treasury_account = frappe.db.get_value("Company", company, "default_cash_account") or "1110 - Cash - EM"
        tech_cash_account = "1115 - Technician Cash Clearing - EM"
        
        # Ensure tech cash account exists
        if not frappe.db.exists("Account", tech_cash_account):
            parent_acc = frappe.db.get_value("Account", {"company": company, "account_type": "Cash", "is_group": 0}, "name") or treasury_account
            acc = frappe.get_doc({
                "doctype": "Account",
                "account_name": "Technician Cash Clearing",
                "parent_account": parent_acc,
                "company": company,
                "account_type": "Cash",
                "is_group": 0
            })
            acc.insert(ignore_permissions=True)
            tech_cash_account = acc.name
            
        je = frappe.get_doc({
            "doctype": "Journal Entry",
            "voucher_type": "Cash Entry",
            "company": company,
            "posting_date": frappe.utils.nowdate(),
            "user_remark": reference_note or f"Cash Transfer from Technician {technician} to Main Treasury",
            "accounts": [
                {
                    "account": treasury_account,
                    "debit_in_account_currency": amt,
                    "credit_in_account_currency": 0
                },
                {
                    "account": tech_cash_account,
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": amt,
                    "party_type": "Employee",
                    "party": technician
                }
            ]
        })
        je.insert(ignore_permissions=True)
        je.submit()
        frappe.db.commit()
        return {"status": "success", "journal_entry": je.name, "amount": amt}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Cash Transfer Error")
        return {"status": "error", "message": str(e)}
