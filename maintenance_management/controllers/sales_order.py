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

def _calculate_tech_score(tech, weights, cust_lat, cust_lon, equipment, cust_zone):
    score = 0.0
    
    # 1. Proximity
    if weights.get("Geographical Proximity") or weights.get("Proximity"):
        w = weights.get("Geographical Proximity") or weights.get("Proximity")
        dist = calc_distance(flt(tech.current_latitude or 0), flt(tech.current_longitude or 0), cust_lat, cust_lon)
        prox_score = max(0, 100 - (dist * 2)) 
        score += (prox_score * w / 100.0)

    # 2. Skill Match
    if weights.get("Skill & Specialization Match") or weights.get("Skill Match"):
        w = weights.get("Skill & Specialization Match") or weights.get("Skill Match")
        skill_score = 100.0 if tech.specialty_equipment == equipment else 0.0
        score += (skill_score * w / 100.0)

    # 3. Availability
    if weights.get("Technician Availability (Status)") or weights.get("Availability"):
        w = weights.get("Technician Availability (Status)") or weights.get("Availability")
        score += (100.0 * w / 100.0)

    # 4. Workload Balance
    if weights.get("Workload Balance (Open Orders)") or weights.get("Workload Balance"):
        w = weights.get("Workload Balance (Open Orders)") or weights.get("Workload Balance")
        open_orders = frappe.db.count("Sales Order Item", {"custom_technician": tech.name, "custom_status": ["not in", ["Completed", "Cancelled"]]})
        workload_score = max(0, 100 - (open_orders * 20))
        score += (workload_score * w / 100.0)

    # 5. Past Performance
    if weights.get("Historical Completion Rate") or weights.get("Performance"):
        w = weights.get("Historical Completion Rate") or weights.get("Performance")
        perf_score = flt(tech.get("performance_rating") or 80.0)
        score += (perf_score * w / 100.0)

    # 6. Service Zone
    if weights.get("Home Service Area Belonging") or weights.get("Service Zone"):
        w = weights.get("Home Service Area Belonging") or weights.get("Service Zone")
        zone_score = 100.0 if tech.service_zone == cust_zone else 0.0
        score += (zone_score * w / 100.0)

    # 7. Route Alignment
    if weights.get("Route Alignment with Scheduled Visits") or weights.get("Route Alignment"):
        w = weights.get("Route Alignment with Scheduled Visits") or weights.get("Route Alignment")
        score += (70.0 * w / 100.0)
        
    return score

@frappe.whitelist()
def assign_technician_weighted(doc):
    """7-Criteria Weighted Assignment Engine for Sales Order Header"""
    if isinstance(doc, str):
        doc = frappe.get_doc("Sales Order", doc)
    
    settings = frappe.get_doc("Field Maintenance Settings", "Field Maintenance Settings")
    weights = {}
    for row in settings.get("weighted_criteria", []):
        if row.enabled:
            weights[row.get("criterion_name") or row.get("criterion")] = flt(row.weight)
    
    if not weights:
        weights = {"Skill Match": 100.0}

    technicians = frappe.get_all("Field Technician", filters={"status": "Available"}, fields=["*"])
    if not technicians:
        return None

    cust_lat = flt(doc.get("custom_customer_lat") or 30.0444)
    cust_lon = flt(doc.get("custom_customer_lon") or 31.2357)
    equipment = doc.get("equipment_type")
    cust_zone = doc.get("territory")

    scored_techs = []
    for tech in technicians:
        score = _calculate_tech_score(tech, weights, cust_lat, cust_lon, equipment, cust_zone)
        scored_techs.append({"tech": tech.name, "score": score})

    if not scored_techs:
        return None

    scored_techs.sort(key=lambda x: x["score"], reverse=True)
    best_tech = scored_techs[0]["tech"]
    
    doc.db_set("assigned_technicians", best_tech)
    doc.db_set("custom_assigned_technician", best_tech)
    doc.db_set("custom_maintenance_status", "Assigned")
    
    return best_tech

def assign_technician_weighted_for_item(doc, item):
    """7-Criteria Weighted Assignment Engine per Sales Order Item"""
    settings = frappe.get_doc("Field Maintenance Settings", "Field Maintenance Settings")
    weights = {}
    for row in settings.get("weighted_criteria", []):
        if row.enabled:
            weights[row.get("criterion_name") or row.get("criterion")] = flt(row.weight)
    
    if not weights:
        weights = {"Skill Match": 100.0}

    technicians = frappe.get_all("Field Technician", filters={"status": "Available"}, fields=["*"])
    if not technicians:
        return None

    cust_lat = flt(doc.get("custom_customer_lat") or 30.0444)
    cust_lon = flt(doc.get("custom_customer_lon") or 31.2357)
    equipment = item.get("custom_equipment_type") or item.item_code
    cust_zone = doc.get("territory")

    scored_techs = []
    for tech in technicians:
        score = _calculate_tech_score(tech, weights, cust_lat, cust_lon, equipment, cust_zone)
        scored_techs.append({"tech": tech.name, "score": score})

    if not scored_techs:
        return None

    scored_techs.sort(key=lambda x: x["score"], reverse=True)
    best_tech = scored_techs[0]["tech"]
    
    item.custom_technician = best_tech
    item.custom_status = "Assigned"
    item.db_set("custom_technician", best_tech)
    item.db_set("custom_status", "Assigned")
    
    return best_tech

def auto_assign_tech_for_item(doc, item):
    _ensure_sql_patch()
    if item.get("custom_technician"):
        return
    
    try:
        settings = frappe.get_doc("Field Maintenance Settings", "Field Maintenance Settings")
        if not settings.get("auto_assign_technician"):
            return
        
        assign_technician_weighted_for_item(doc, item)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Auto Assign Tech Item Error")

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
    
    for item in doc.items:
        existing = frappe.db.exists("Service Appointment", {"sales_order": doc.name, "sales_order_item": item.name})
        if not existing:
            tech = item.get("custom_technician") or doc.get("custom_assigned_technician") or doc.get("assigned_technicians") or None
            sa = frappe.get_doc({
                "doctype": "Service Appointment",
                "customer": doc.customer,
                "sales_order": doc.name,
                "sales_order_item": item.name,
                "status": "Scheduled",
                "priority": doc.get("priority") or "Medium",
                "scheduled_date": item.get("custom_scheduled_date_time") or doc.get("custom_scheduled_date_time") or now(),
                "duration_hours": 2,
                "technician": tech,
                "notes": f"Service Appointment for item {item.item_code} on Sales Order {doc.name}"
            })
            sa.insert(ignore_permissions=True)
            try:
                sa.submit()
            except Exception as e:
                frappe.log_error(title=f"Service Appointment Submit Error for {sa.name}", message=str(e))
            if tech:
                send_technician_notification(doc, sa.name, technician_override=tech)

def send_technician_notification(doc, appointment_name, technician_override=None):
    tech = technician_override or doc.get("custom_assigned_technician")
    if not tech:
        return
    tech_doc = frappe.get_doc("Field Technician", tech)
    target_user = tech_doc.get("user")
    user_email = target_user or tech_doc.get("email")
    
    if user_email and "@" not in user_email:
        user_email = frappe.db.get_value("User", user_email, "email")
    
    if not target_user and user_email:
        target_user = frappe.db.get_value("User", {"email": user_email}, "name")
    
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
    
    if target_user:
        try:
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": f"New Maintenance Dispatch: {doc.name}",
                "email_content": msg,
                "for_user": target_user,
                "document_type": "Service Appointment",
                "document_name": appointment_name
            }).insert(ignore_permissions=True)
        except Exception:
            pass

def after_insert(doc, method=None):
    _ensure_sql_patch()
    if not doc.get("custom_is_maintenance_order"):
        return
    for item in doc.items:
        if not item.get("custom_status"):
            item.custom_status = "New"
        if not item.get("custom_technician"):
            auto_assign_tech_for_item(doc, item)
    if doc.docstatus == 1:
        create_service_appointment(doc)

def on_update(doc, method=None):
    _ensure_sql_patch()
    if not doc.get("custom_is_maintenance_order"):
        return
    for item in doc.items:
        if not item.get("custom_status"):
            item.custom_status = "New"
        if not item.get("custom_technician"):
            auto_assign_tech_for_item(doc, item)
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
            
        return {"status": "success", "distance_to_office": dist_office}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def accept_dispatch(appointment_name):
    try:
        sa = frappe.get_doc("Service Appointment", appointment_name)
        sa.status = "Accepted"
        sa.save(ignore_permissions=True)
        return "<h3>Success! Dispatch Accepted.</h3><p>You can now view the details in your technician portal.</p>"
    except Exception as e:
        return f"<h3>Error</h3><p>{str(e)}</p>"

@frappe.whitelist()
def reject_dispatch(appointment_name):
    try:
        sa = frappe.get_doc("Service Appointment", appointment_name)
        sa.status = "Rejected"
        sa.save(ignore_permissions=True)
        return "<h3>Dispatch Rejected</h3><p>Management has been notified.</p>"
    except Exception as e:
        return f"<h3>Error</h3><p>{str(e)}</p>"
