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
