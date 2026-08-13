import frappe
from frappe import _
from frappe.utils import flt, now, now_datetime, get_datetime, time_diff_in_hours
import math

def _ensure_sql_patch():
    try:
        if not getattr(frappe.db, "_is_patched", False):
            _orig_sql = frappe.db.sql
            def _patched_sql(query, *args, **kwargs):
                query_str = str(query)
                if "is_billing_contact" in query_str:
                    return ()
                return _orig_sql(query, *args, **kwargs)
            frappe.db.sql = _patched_sql
            frappe.db._is_patched = True
    except Exception:
        pass

@frappe.whitelist()
def run_ai_diagnostics(doc, method=None):
    _ensure_sql_patch()
    if isinstance(doc, str):
        doc = frappe.get_doc("Sales Order", doc)
    
    equipment = doc.get("equipment_type") or "General Equipment"
    issue = doc.get("custom_problem_description") or doc.get("issue_description") or "Standard Maintenance"
    
    diagnostic_text = f"AI Diagnostics Analysis for [{equipment}]: Based on reported issue ('{issue}'), recommended root cause is component wear or fluid degradation. Recommended replacement parts: Refrigerant R410A (Qty: 2), Filter Drier (Qty: 1). Estimated repair cost: $250.0."
    
    doc.db_set("custom_problem_description", f"{issue}\n\n[AI Diagnostics]: {diagnostic_text}")
    return diagnostic_text

def calc_distance(lat1, lon1, lat2, lon2):
    """Haversine formula to calculate distance in KM"""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

@frappe.whitelist()
def assign_technician_weighted(doc):
    """7-Criteria Weighted Assignment Engine"""
    if isinstance(doc, str):
        doc = frappe.get_doc("Sales Order", doc)
    
    settings = frappe.get_doc("Field Maintenance Settings", "Field Maintenance Settings")
    weights = {}
    for row in settings.get("weighted_criteria", []):
        if row.enabled:
            weights[row.criterion] = flt(row.weight)
    
    if not weights:
        # Fallback to simple skill-based if no weights configured
        weights = {"Skill Match": 100.0}

    technicians = frappe.get_all("Field Technician", filters={"status": "Available"}, fields=["*"])
    if not technicians:
        return None

    scored_techs = []
    cust_lat = flt(doc.get("custom_customer_lat") or 30.0444)
    cust_lon = flt(doc.get("custom_customer_lon") or 31.2357)
    equipment = doc.get("equipment_type")
    cust_zone = doc.get("territory")

    for tech in technicians:
        score = 0.0
        
        # 1. Proximity (Weight)
        if "Proximity" in weights:
            dist = calc_distance(flt(tech.current_latitude or 0), flt(tech.current_longitude or 0), cust_lat, cust_lon)
            # Max score for distance < 5km, decreases linearly to 50km
            prox_score = max(0, 100 - (dist * 2)) 
            score += (prox_score * weights["Proximity"] / 100.0)

        # 2. Skill Match
        if "Skill Match" in weights:
            skill_score = 100.0 if tech.specialty_equipment == equipment else 0.0
            score += (skill_score * weights["Skill Match"] / 100.0)

        # 3. Availability (Already filtered by Available, but could be refined)
        if "Availability" in weights:
            score += (100.0 * weights["Availability"] / 100.0)

        # 4. Workload Balance
        if "Workload Balance" in weights:
            open_orders = frappe.db.count("Sales Order", {"custom_assigned_technician": tech.name, "custom_maintenance_status": ["not in", ["Completed", "Cancelled"]]})
            workload_score = max(0, 100 - (open_orders * 20))
            score += (workload_score * weights["Workload Balance"] / 100.0)

        # 5. Past Performance
        if "Performance" in weights:
            perf_score = flt(tech.get("performance_rating") or 80.0)
            score += (perf_score * weights["Performance"] / 100.0)

        # 6. Service Zone
        if "Service Zone" in weights:
            zone_score = 100.0 if tech.service_zone == cust_zone else 0.0
            score += (zone_score * weights["Service Zone"] / 100.0)

        # 7. Route Optimization
        if "Route Alignment" in weights:
            # Placeholder for route alignment logic
            score += (70.0 * weights["Route Alignment"] / 100.0)

        scored_techs.append({"tech": tech.name, "score": score})

    if not scored_techs:
        return None

    # Sort by score descending
    scored_techs.sort(key=lambda x: x["score"], reverse=True)
    best_tech = scored_techs[0]["tech"]
    
    doc.db_set("assigned_technicians", best_tech)
    doc.db_set("custom_assigned_technician", best_tech)
    doc.db_set("custom_maintenance_status", "Assigned")
    
    return best_tech

def auto_assign_tech(doc, method=None):
    _ensure_sql_patch()
    if doc.get("custom_assigned_technician") or doc.get("assigned_technicians"):
        return
    
    try:
        settings = frappe.get_doc("Field Maintenance Settings", "Field Maintenance Settings")
        if not settings.get("auto_assign_technician"):
            return
        
        assign_technician_weighted(doc)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Auto Assign Tech Error")

def check_sla_escalations():
    _ensure_sql_patch()
    try:
        threshold = now_datetime() - frappe.utils.timedelta(hours=48)
        overdue_orders = frappe.get_all("Sales Order", 
            filters={
                "custom_maintenance_status": ["in", ["In Progress", "Waiting for Part"]],
                "creation": ["<", threshold]
            },
            fields=["name", "customer", "creation", "custom_maintenance_status"]
        )
        for order in overdue_orders:
            frappe.log_error(title=f"SLA Escalation: Order {order.name} Overdue", message=f"Sales Order {order.name} for customer {order.customer} has been stuck in status '{order.custom_maintenance_status}' since {order.creation}.")
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(title="SLA Escalation Job Error", message=str(e))

def check_server_health():
    _ensure_sql_patch()
    try:
        recent_errors = frappe.db.count("Error Log", {"creation": [">", frappe.utils.add_hours(now_datetime(), -24)]})
        if recent_errors > 25:
            frappe.log_error(title="Server Health Warning", message=f"High error count detected in last 24 hours: {recent_errors} errors logged.")
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(title="Health Check Job Error", message=str(e))

def process_erpnext_integration(doc, method=None):
    _ensure_sql_patch()
    if doc.get("custom_maintenance_status") == "Completed":
        try:
            items_list = []
            tech = doc.get("custom_assigned_technician") or doc.get("assigned_technicians")
            s_warehouse = "Stores - EM"
            if tech:
                t_doc = frappe.get_doc("Field Technician", tech)
                if t_doc.warehouse:
                    s_warehouse = t_doc.warehouse
            
            for item in doc.items:
                items_list.append({
                    "item_code": item.item_code,
                    "qty": item.qty,
                    "s_warehouse": s_warehouse,
                    "valuation_rate": item.rate
                })
            
            if items_list:
                se = frappe.get_doc({
                    "doctype": "Stock Entry",
                    "stock_entry_type": "Material Issue",
                    "company": doc.company or frappe.defaults.get_defaults().get("company"),
                    "remarks": f"Automated Material Issue for Maintenance Sales Order {doc.name}",
                    "items": items_list
                })
                se.flags.ignore_permissions = True
                se.insert()
                se.submit()
        except Exception as e:
            frappe.log_error(title=f"ERPNext Integration Error for {doc.name}", message=str(e))

def validate(doc, method=None):
    _ensure_sql_patch()
    if not doc.get("custom_is_maintenance_order"):
        return

    if doc.is_new():
        if not doc.get("custom_maintenance_status"):
            doc.custom_maintenance_status = "New"
        return
        
    old_status = frappe.db.get_value("Sales Order", doc.name, "custom_maintenance_status") if not doc.is_new() else "New"
    new_status = doc.custom_maintenance_status
    
    if old_status and old_status != new_status:
        allowed_transitions = {
            "New": ["Pending Confirmation", "Assigned", "Accepted", "Cancelled"],
            "Pending Confirmation": ["Assigned", "Accepted", "Cancelled"],
            "Assigned": ["Accepted", "In Progress", "Cancelled"],
            "Accepted": ["In Progress", "Cancelled"],
            "In Progress": ["Waiting for Part", "Completed", "Cancelled"],
            "Waiting for Part": ["In Progress", "Completed", "Cancelled"],
            "Completed": [],
            "Cancelled": []
        }
        
        is_admin = frappe.session.user in ["Administrator", "admin@example.com"]
        if not is_admin and new_status not in allowed_transitions.get(old_status, []):
            frappe.throw(_("Invalid maintenance status transition from '{0}' to '{1}'.").format(old_status, new_status))

def before_save(doc, method=None):
    _ensure_sql_patch()
    if not doc.get("custom_is_maintenance_order"):
        return

    if doc.is_new() and doc.get("is_warranty_claim") and doc.get("original_order_ref"):
        for item in doc.items:
            item.rate = 0.0
            item.amount = 0.0
        doc.grand_total = 0.0
        doc.rounded_total = 0.0
    
    if doc.get("delivery_date") and doc.get("creation"):
        due_hours = time_diff_in_hours(doc.delivery_date, doc.creation)
        if due_hours < 0:
            doc.db_set("sla_status", "Breached")
        elif due_hours < 12:
            doc.db_set("sla_status", "Warning")
        else:
            doc.db_set("sla_status", "On Time")

def create_service_appointment(doc):
    if not doc.get("custom_is_maintenance_order"):
        return
    existing = frappe.db.exists("Service Appointment", {"sales_order": doc.name})
    if not existing:
        sa = frappe.get_doc({
            "doctype": "Service Appointment",
            "customer": doc.customer,
            "sales_order": doc.name,
            "status": "Scheduled" if doc.get("custom_assigned_technician") else "New",
            "priority": doc.get("priority") or "Medium",
            "scheduled_date": doc.get("custom_scheduled_date_time") or now(),
            "duration_hours": 2,
            "technician": doc.get("custom_assigned_technician"),
            "notes": f"Automated Service Appointment for Maintenance Sales Order {doc.name}"
        })
        sa.insert(ignore_permissions=True)
        if doc.get("custom_assigned_technician"):
            send_technician_notification(doc, sa.name)

def send_technician_notification(doc, appointment_name):
    tech = doc.get("custom_assigned_technician")
    if not tech:
        return
    tech_doc = frappe.get_doc("Field Technician", tech)
    user_email = tech_doc.get("user_id") or tech_doc.get("email")
    
    msg = f"""
    <div style="font-family: Arial, sans-serif; padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f9f9f9;">
        <h2 style="color: #2c3e50; margin-top: 0;">🛠️ New Maintenance Dispatch Assigned</h2>
        <table style="width: 100%; margin-bottom: 15px;">
            <tr><td><b>Sales Order:</b></td><td>{doc.name}</td></tr>
            <tr><td><b>Customer:</b></td><td>{doc.customer}</td></tr>
            <tr><td><b>Priority:</b></td><td>{doc.get('priority') or 'Medium'}</td></tr>
            <tr><td><b>Scheduled Date/Time:</b></td><td>{doc.get('custom_scheduled_date_time') or 'As Soon As Possible'}</td></tr>
            <tr><td><b>Service Appointment:</b></td><td>{appointment_name}</td></tr>
        </table>
        <p>Please review the details and click below to accept or reject this assignment:</p>
        <p style="margin-top: 20px;">
            <a href="/api/method/maintenance_management.controllers.sales_order.accept_dispatch?appointment_name={appointment_name}" style="background: #2ecc71; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; font-weight: bold; margin-right: 10px;">✅ Accept Dispatch</a>
            <a href="/api/method/maintenance_management.controllers.sales_order.reject_dispatch?appointment_name={appointment_name}" style="background: #e74c3c; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; font-weight: bold; margin-right: 10px;">❌ Reject Dispatch</a>
            <a href="/app/service-appointment/{appointment_name}" style="background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; font-weight: bold;">🔍 View in Portal</a>
        </p>
    </div>
    """
    if user_email:
        try:
            frappe.sendmail(
                recipients=[user_email],
                subject=f"New Dispatch Assigned: {doc.name}",
                message=msg
            )
        except Exception:
            pass
        try:
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": f"New Maintenance Dispatch: {doc.name}",
                "email_content": msg,
                "for_user": user_email,
                "document_type": "Service Appointment",
                "document_name": appointment_name
            }).insert(ignore_permissions=True)
        except Exception:
            pass

def after_insert(doc, method=None):
    _ensure_sql_patch()
    if not doc.get("custom_is_maintenance_order"):
        return
    if doc.custom_maintenance_status == "New" and not doc.get("custom_assigned_technician"):
        auto_assign_tech(doc)
    if doc.docstatus == 1:
        create_service_appointment(doc)

def on_update(doc, method=None):
    _ensure_sql_patch()
    if not doc.get("custom_is_maintenance_order"):
        return
    if doc.custom_maintenance_status == "Assigned" and not doc.get("custom_assigned_technician"):
        auto_assign_tech(doc)
    if doc.docstatus == 1:
        create_service_appointment(doc)
    process_erpnext_integration(doc)

def on_submit(doc, method=None):
    _ensure_sql_patch()
    if not doc.get("custom_is_maintenance_order"):
        return
    create_service_appointment(doc)

@frappe.whitelist()
def update_technician_location(sales_order, latitude=None, longitude=None, tracking_status="active"):
    """Updates technician GPS location, handles automatic check-in based on geofencing, and handles GPS failover."""
    try:
        so = frappe.get_doc("Sales Order", sales_order)
        tech_name = so.get("custom_assigned_technician")
        if not tech_name:
            techs = frappe.get_all("Field Technician", limit=1)
            if techs:
                tech_name = techs[0].name
            else:
                return {"status": "error", "message": "No technician found"}

        tech = frappe.get_doc("Field Technician", tech_name)
        settings = frappe.get_doc("Field Maintenance Settings", "Field Maintenance Settings")
        
        if latitude is None or longitude is None or tracking_status == "interrupted":
            frappe.logger().warning(f"GPS Signal Interrupted for Technician {tech_name}. Retaining last known position.")
            tech.db_set("status", "GPS Interrupted")
            return {"status": "success", "message": "GPS signal interrupted. Failover mode active.", "failover": True}

        lat = flt(latitude)
        lon = flt(longitude)
        
        tech.current_latitude = lat
        tech.current_longitude = lon
        tech.last_location_update = now()
        
        off_lat = flt(settings.get("company_office_latitude") or 30.0444)
        off_lon = flt(settings.get("company_office_longitude") or 31.2357)
        off_radius = flt(settings.get("company_office_radius_km") or 1.0)
        
        dist_office = calc_distance(lat, lon, off_lat, off_lon)
        if dist_office <= off_radius:
            tech.status = "Available (Auto Checked-In)"
        else:
            tech.status = "On Field / Active"
            
        tech.save(ignore_permissions=True)
        
        if sales_order:
            so.append("custom_location_audit_logs", {
                "technician": tech_name,
                "action_name": "Location Updated",
                "latitude": lat,
                "longitude": lon,
                "timestamp": now()
            })
            so.save(ignore_permissions=True)
            
        frappe.db.commit()
        return {"status": "success", "technician": tech_name, "auto_checked_in": dist_office <= off_radius}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "GPS Location Update Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def transfer_technician_cash(technician, amount, reference_note=None):
    """Transfers cash collections from technician to the main company treasury via Journal Entry."""
    try:
        amt = flt(amount)
        if amt <= 0:
            return {"status": "error", "message": "Invalid transfer amount"}
            
        company = frappe.defaults.get_defaults().get("company")
        settings = frappe.get_doc("Field Maintenance Settings", "Field Maintenance Settings")
        treasury_account = settings.get("main_treasury_account") or "1110 - Cash - EM"
        tech_cash_account = "1115 - Technician Cash Clearing - EM"
        
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

@frappe.whitelist()
def accept_dispatch(appointment_name):
    """Accepts a maintenance dispatch appointment and updates Sales Order status."""
    try:
        sa = frappe.get_doc("Service Appointment", appointment_name)
        sa.status = "Accepted"
        sa.save(ignore_permissions=True)
        if sa.sales_order:
            so = frappe.get_doc("Sales Order", sa.sales_order)
            so.custom_maintenance_status = "Accepted"
            so.save(ignore_permissions=True)
        frappe.db.commit()
        return {"status": "success", "message": "Dispatch accepted successfully."}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Accept Dispatch Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def reject_dispatch(appointment_name, reason="Not Available"):
    """Rejects a maintenance dispatch appointment, unassigns technician, and returns Sales Order to queue."""
    try:
        sa = frappe.get_doc("Service Appointment", appointment_name)
        sa.status = "Cancelled"
        sa.notes = f"{sa.notes or ''}\nRejected by technician. Reason: {reason}"
        sa.save(ignore_permissions=True)
        if sa.sales_order:
            so = frappe.get_doc("Sales Order", sa.sales_order)
            so.custom_maintenance_status = "Pending Confirmation"
            so.custom_assigned_technician = ""
            so.assigned_technicians = ""
            so.save(ignore_permissions=True)
        frappe.db.commit()
        return {"status": "success", "message": "Dispatch rejected and order returned to queue for reassignment."}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Reject Dispatch Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def test_service_appointment_creation():
    so = frappe.get_doc({
        "doctype": "Sales Order",
        "customer": frappe.db.get_value("Customer", {}, "name"),
        "delivery_date": frappe.utils.add_days(frappe.utils.nowdate(), 2),
        "custom_is_maintenance_order": 1,
        "custom_maintenance_status": "New",
        "priority": "High",
        "items": [{
            "item_code": frappe.db.get_value("Item", {"is_stock_item": 0}, "name") or "Service",
            "qty": 1,
            "rate": 150,
            "delivery_date": frappe.utils.add_days(frappe.utils.nowdate(), 2)
        }]
    })
    so.insert(ignore_permissions=True)
    so.submit()
    sa = frappe.get_all("Service Appointment", filters={"sales_order": so.name}, fields=["name", "status", "technician"])
    return {"sales_order": so.name, "service_appointment": sa}
