import frappe
from frappe import _
from frappe.utils import flt, now, now_datetime, time_diff_in_hours, get_url
import math

def _ensure_sql_patch():
    """Ensures necessary SQL indexes exist for performance"""
    try:
        frappe.db.sql("""
            ALTER TABLE `tabSales Order Item` 
            ADD INDEX IF NOT EXISTS `idx_custom_tech_status` (custom_technician, custom_status)
        """)
    except Exception:
        pass

def calc_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
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
    doc.db_set("custom_maintenance_status", "Scheduled")
    
    return best_tech

def assign_technician_weighted_for_item(doc, item):
    """7-Criteria Weighted Assignment Engine per Sales Order Item"""
    try:
        settings = frappe.get_doc("Field Maintenance Settings", "Field Maintenance Settings")
    except frappe.DoesNotExistError:
        settings = frappe.get_single("Field Maintenance Settings")
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
    item.custom_status = "Scheduled"
    item.db_set("custom_technician", best_tech)
    item.db_set("custom_status", "Scheduled")
    
    return best_tech

def auto_assign_tech_for_item(doc, item):
    """Fallback auto-assignment logic for items"""
    try:
        best_tech = assign_technician_weighted_for_item(doc, item)
        if best_tech:
            item.custom_technician = best_tech
            item.custom_status = "Scheduled"
            item.db_set("custom_technician", best_tech)
            item.db_set("custom_status", "Scheduled")
    except Exception:
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
        # Fallback to first available tech if none assigned
        techs = frappe.get_all("Field Technician", limit=1)
        if techs:
            tech = techs[0].name
        else:
            return

    tech_doc = frappe.get_doc("Field Technician", tech)
    target_user = tech_doc.get("user") or "Administrator"
    user_email = frappe.db.get_value("User", target_user, "email")
    
    try:
        settings = frappe.get_doc("Field Maintenance Settings", "Field Maintenance Settings")
    except frappe.DoesNotExistError:
        settings = frappe.get_single("Field Maintenance Settings")
    title_tpl = settings.get("notification_title_template") or "🛠️ New Dispatch: {sales_order}"
    msg_tpl = settings.get("notification_message_template") or "Customer: {customer}\nTime: {time}"
    sound_effect = settings.get("notification_sound") or "Chime"
    
    formatted_title = title_tpl.format(sales_order=doc.name, customer=doc.customer_name or doc.customer)
    formatted_msg = msg_tpl.format(sales_order=doc.name, customer=doc.customer_name or doc.customer, time=doc.get('custom_scheduled_date_time') or 'Immediate')
    
    msg = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; padding: 10px; background: #fff; border-left: 3px solid #1a73e8; border-radius: 4px; max-width: 320px;">
        <div style="font-weight: 600; font-size: 14px; color: #1f2937; margin-bottom: 4px;">{formatted_title}</div>
        <div style="font-size: 12px; color: #4b5563; margin-bottom: 10px; line-height: 1.4;">
            {formatted_msg}
        </div>
        <div style="display: flex; gap: 6px;">
            <a href="{get_url()}/api/method/maintenance_management.controllers.sales_order.accept_dispatch?appointment_name={appointment_name}" 
               style="background: #10b981; color: #fff; padding: 4px 10px; text-decoration: none; border-radius: 4px; font-size: 11px; font-weight: 500;">
               Accept
            </a>
            <a href="{get_url()}/api/method/maintenance_management.controllers.sales_order.reject_dispatch?appointment_name={appointment_name}" 
               style="background: #ef4444; color: #fff; padding: 4px 10px; text-decoration: none; border-radius: 4px; font-size: 11px; font-weight: 500;">
               Reject
            </a>
            <a href="{get_url()}/app/service-appointment/{appointment_name}" 
               style="background: #3b82f6; color: #fff; padding: 4px 10px; text-decoration: none; border-radius: 4px; font-size: 11px; font-weight: 500;">
               Details
            </a>
        </div>
    </div>
    """
    if user_email:
        try:
            frappe.sendmail(
                recipients=[user_email],
                subject=f"Dispatch: {doc.name}",
                message=msg
            )
        except Exception:
            pass
    
    if target_user:
        try:
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": f"New Dispatch: {doc.name}",
                "email_content": msg,
                "for_user": target_user,
                "document_type": "Service Appointment",
                "document_name": appointment_name
            }).insert(ignore_permissions=True)
            
            # Real-time notification with sound & mobile push
            frappe.publish_realtime(
                "maintenance_notification",
                {
                    "title": formatted_title,
                    "message": formatted_msg,
                    "docname": appointment_name,
                    "sound": sound_effect,
                    "sound_file": settings.notification_sound_file,
                    "push": True
                },
                user=target_user,
                after_commit=True
            )
            
            # Mobile Push Notification (Standard Frappe)
            if settings.enable_mobile_push:
                try:
                    from frappe.utils.response import json_handler
                    frappe.publish_realtime(
                        "notification",
                        {
                            "title": formatted_title,
                            "body": formatted_msg,
                            "document_type": "Service Appointment",
                            "document_name": appointment_name
                        },
                        user=target_user,
                        after_commit=True
                    )
                except Exception:
                    pass
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
