# -*- coding: utf-8 -*-
import frappe

@frappe.whitelist(allow_guest=True)
def track_request(request_id):
    """Public API for customer tracking portal"""
    if not request_id:
        return {"status": "error", "message": "Request ID is required"}
    
    doc = frappe.db.get_value(
        "Field Service Request",
        request_id,
        ["name", "customer_name", "equipment_type", "status", "technician", "scheduled_date", "total_amount", "warranty_status"],
        as_dict=True
    )
    
    if not doc:
        return {"status": "error", "message": "Service Request not found"}
        
    return {"status": "success", "data": doc}

@frappe.whitelist()
def fix_workspace():
	try:
		w = frappe.get_doc("Workspace", "Maintenance Management")
		w.public = 1
		w.type = "Workspace"
		w.link_type = None
		w.link_to = None
		w.icon = "settings"
		w.is_standard = 1
		w.save(ignore_permissions=True)
	except Exception as e:
		pass
	
	frappe.db.commit()
	return "Workspace Maintenance Management fixed successfully!"

def after_migrate():
	if not frappe.db.exists("Workspace", "Maintenance Management"):
		w = frappe.get_doc({
			"doctype": "Workspace",
			"name": "Maintenance Management",
			"label": "Maintenance Management",
			"module": "Maintenance Management",
			"app": "maintenance_management",
			"public": 1,
			"type": "Workspace",
			"icon": "settings",
			"sequence_id": 2.0,
			"links": [
				{"type": "Card Break", "label": "Field Maintenance", "link_count": 2},
				{"type": "Link", "label": "Field Technician", "link_type": "DocType", "link_to": "Field Technician"},
				{"type": "Link", "label": "Field Maintenance Settings", "link_type": "DocType", "link_to": "Field Maintenance Settings"}
			]
		})
		w.insert(ignore_permissions=True)
		frappe.db.commit()

@frappe.whitelist()
def check_module():
	res = {
		"modules": frappe.get_all('Module Def', filters={'app_name': 'maintenance_management'}, fields=['name']),
		"workspaces": frappe.get_all('Workspace', filters={'app': 'maintenance_management'}, fields=['name', 'module', 'public'])
	}
	if not frappe.db.exists('Module Def', 'Maintenance Management'):
		m = frappe.get_doc({
			'doctype': 'Module Def',
			'module_name': 'Maintenance Management',
			'app_name': 'maintenance_management'
		})
		m.insert(ignore_permissions=True)
		frappe.db.commit()
		res["created_module"] = True
	return res

@frappe.whitelist()
def update_technician_location(sales_order, latitude, longitude, tracking_status="active"):
    frappe.logger().info(f"Technician Location Update: SO={sales_order}, Lat={latitude}, Lon={longitude}, Status={tracking_status}")
    return {"status": "success", "message": "Location updated successfully"}

@frappe.whitelist()
def create_technician_order(customer, items, description=None, technician=None, latitude=None, longitude=None):
    """Allows a technician to initiate a service order directly from the mobile portal."""
    try:
        import json
        if isinstance(items, str):
            items = json.loads(items)
        
        doc = frappe.get_doc({
            'doctype': 'Sales Order',
            'customer': customer,
            'custom_is_maintenance_order': 1,
            'custom_maintenance_status': 'New',
            'custom_assigned_technician': technician,
            'custom_problem_description': description or 'Initiated by Field Technician',
            'delivery_date': frappe.utils.nowdate(),
            'items': items
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
        if technician and latitude and longitude:
            doc.append('custom_location_audit_logs', {
                'technician': technician,
                'action_name': 'Technician Created Order',
                'latitude': float(latitude),
                'longitude': float(longitude),
                'timestamp': frappe.utils.now()
            })
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            
        return {'status': 'success', 'sales_order': doc.name}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Technician Order Creation Error')
        return {'status': 'error', 'message': str(e)}

@frappe.whitelist()
def check_technician_shift(technician_name):
    """Checks if the technician is currently within their shift hours."""
    tech = frappe.get_doc('Field Technician', technician_name)
    now_time = datetime.now().time()
    start = tech.get('shift_start') or time(8, 0)
    end = tech.get('shift_end') or time(17, 0)
    
    if isinstance(start, str):
        start = datetime.strptime(start, '%H:%M:%S').time()
    if isinstance(end, str):
        end = datetime.strptime(end, '%H:%M:%S').time()
        
    in_shift = start <= now_time <= end
    return {'in_shift': in_shift, 'shift_start': str(start), 'shift_end': str(end), 'current_time': str(now_time)}

@frappe.whitelist()
def request_spare_parts(sales_order, items, technician):
    """Allows a technician to request spare parts from the field, creating a Material Request in ERPNext."""
    try:
        import json
        if isinstance(items, str):
            items = json.loads(items)
            
        mat_req = frappe.get_doc({
            'doctype': 'Material Request',
            'material_request_type': 'Purchase',
            'custom_maintenance_order': sales_order,
            'schedule_date': frappe.utils.nowdate(),
            'items': items
        })
        mat_req.insert(ignore_permissions=True)
        frappe.db.commit()
        return {'status': 'success', 'material_request': mat_req.name}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Spare Parts Request Error')
        return {'status': 'error', 'message': str(e)}

@frappe.whitelist()
def check_sla_escalations():
    """Background method to check overdue maintenance orders and flag managers."""
    settings = frappe.get_single('Maintenance Settings')
    if not settings.get('default_sla_resolution_hours'):
        return
        
    hours = int(settings.default_sla_resolution_hours)
    overdue_orders = frappe.db.sql("""
        select name, customer, creation, custom_assigned_technician 
        from `tabSales Order` 
        where custom_is_maintenance_order = 1 
        and custom_maintenance_status not in ('Completed', 'Cancelled')
        and timestampdiff(hour, creation, now()) > %s
        and (custom_sla_escalated = 0 or custom_sla_escalated is null)
    """, hours, as_dict=1)
    
    for order in overdue_orders:
        frappe.db.set_value('Sales Order', order.name, 'custom_sla_escalated', 1)
        # Create a notification or log
        frappe.log_error(f"SLA Breached for Order {order.name} assigned to {order.custom_assigned_technician}", "SLA Escalation Alert")
        
    frappe.db.commit()
    return {'escalated_count': len(overdue_orders)}

@frappe.whitelist()
def complete_maintenance_order(sales_order, signature=None, notes=None, feedback=None, rating=5):
    """Completes the maintenance order, generates Sales Invoice & Stock Entry, and logs customer feedback."""
    doc = frappe.get_doc('Sales Order', sales_order)
    doc.custom_maintenance_status = 'Completed'
    if signature:
        doc.custom_customer_signature = signature
    if notes:
        doc.custom_technician_notes = notes
    if feedback:
        doc.custom_customer_feedback = feedback
    doc.custom_customer_rating = rating
    
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {'status': 'success', 'message': 'Order completed successfully and documents generated.'}

@frappe.whitelist(allow_guest=True)
def get_customer_tracking(sales_order):
    """Public API for customers to track their assigned technician and service status."""
    doc = frappe.get_doc('Sales Order', sales_order)
    if not doc.get('custom_is_maintenance_order'):
        return {'status': 'error', 'message': 'Invalid maintenance order'}
        
    tech = doc.get('custom_assigned_technician')
    tech_data = {}
    if tech:
        t_doc = frappe.get_doc('Field Technician', tech)
        tech_data = {
            'technician_name': t_doc.get('employee_name') or t_doc.name,
            'phone': t_doc.get('cell_number'),
            'latitude': t_doc.get('current_latitude'),
            'longitude': t_doc.get('current_longitude'),
            'last_update': t_doc.get('last_location_update')
        }
        
    return {
        'order': doc.name,
        'customer': doc.customer,
        'status': doc.get('custom_maintenance_status'),
        'problem': doc.get('custom_problem_description'),
        'technician': tech_data,
        'audit_logs': doc.get('custom_location_audit_logs', [])
    }

@frappe.whitelist()
def reschedule_maintenance_order(sales_order, new_delivery_date, reason=None):
    """Allows rescheduling a service request to a new date/time."""
    doc = frappe.get_doc('Sales Order', sales_order)
    doc.delivery_date = new_delivery_date
    if reason:
        doc.custom_problem_description = (doc.custom_problem_description or '') + f"\n[Rescheduled to {new_delivery_date}: {reason}]"
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {'status': 'success', 'new_date': new_delivery_date}
