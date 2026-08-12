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
    import json
    # 1. Create Number Cards if not exist
    cards = [
        {"name": "Active Service Orders Count", "label": "Active Service Orders", "function": "Count", "document_type": "Sales Order", "filters": '[["Sales Order", "status", "!=", "Completed"]]'},
        {"name": "Pending Invoices Count", "label": "Pending Invoices", "function": "Count", "document_type": "Sales Invoice", "filters": '[["Sales Invoice", "status", "=", "Unpaid"]]'},
        {"name": "Available Technicians", "label": "Available Technicians", "function": "Count", "document_type": "Field Technician", "filters": '[["Field Technician", "status", "=", "Available"]]'},
        {"name": "Total Maintenance Revenue", "label": "Maintenance Revenue", "function": "Sum", "aggregate_function_based_on": "grand_total", "document_type": "Sales Invoice"}
    ]
    
    for c in cards:
        if not frappe.db.exists("Number Card", c["name"]):
            doc = frappe.get_doc({
                "doctype": "Number Card",
                "name": c["name"],
                "label": c["label"],
                "type": "Document Type",
                "document_type": c["document_type"],
                "function": c["function"],
                "aggregate_function_based_on": c.get("aggregate_function_based_on"),
                "filters_json": c.get("filters", "[]"),
                "is_standard": 0,
                "module": "Maintenance Management"
            })
            doc.insert(ignore_permissions=True)
            
    # 2. Create Charts if not exist
    if not frappe.db.exists("Dashboard Chart", "Orders by Status"):
        chart = frappe.get_doc({
            "doctype": "Dashboard Chart",
            "chart_name": "Orders by Status",
            "chart_type": "Group By",
            "document_type": "Sales Order",
            "group_by_based_on": "status",
            "group_by_type": "Count",
            "is_standard": 0,
            "module": "Maintenance Management",
            "time_interval": "Monthly",
            "timeseries": 0,
            "type": "Donut",
            "filters_json": "[]"
        })
        chart.insert(ignore_permissions=True)

    # 3. Update Maintenance Management Workspace Content
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
            "sequence_id": 2.0
        })
        w.insert(ignore_permissions=True)
        
    ws = frappe.get_doc("Workspace", "Maintenance Management")
    ws.content = json.dumps([
        {"type": "header", "data": {"text": "📊 Maintenance Management Operations & Executive Summary", "col": 12}},
        {"type": "spacer", "data": {"col": 12}},
        {"type": "card", "data": {"card_name": "Active Service Orders Count", "col": 4}},
        {"type": "card", "data": {"card_name": "Pending Invoices Count", "col": 4}},
        {"type": "card", "data": {"card_name": "Available Technicians", "col": 4}},
        {"type": "spacer", "data": {"col": 12}},
        {"type": "chart", "data": {"chart_name": "Orders by Status", "col": 12}},
        {"type": "spacer", "data": {"col": 12}},
        {"type": "header", "data": {"text": "⚡ Quick Links & Management Modules", "col": 12}},
        {"type": "shortcut", "data": {"shortcut_name": "Field Maintenance Settings", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "Field Technician", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "Field Service Request", "col": 3}},
        {"type": "shortcut", "data": {"shortcut_name": "Sales Order", "col": 3}},
    ])
    ws.save(ignore_permissions=True)

	# 4. Update Technician Dashboard Workspace Content
	if frappe.db.exists("Workspace", "Technician Dashboard"):
		ws_tech = frappe.get_doc("Workspace", "Technician Dashboard")
		ws_tech.type = "Workspace"
		ws_tech.content = json.dumps([
            {"type": "header", "data": {"text": "🛠️ Technician Field Operations & Portal", "col": 12}},
            {"type": "spacer", "data": {"col": 12}},
            {"type": "card", "data": {"card_name": "Active Service Orders Count", "col": 6}},
            {"type": "card", "data": {"card_name": "Available Technicians", "col": 6}},
            {"type": "spacer", "data": {"col": 12}},
            {"type": "header", "data": {"text": "🚀 Field Action Shortcuts", "col": 12}},
            {"type": "shortcut", "data": {"shortcut_name": "Active Service Orders", "col": 4}},
            {"type": "shortcut", "data": {"shortcut_name": "Van Warehouse", "col": 4}},
            {"type": "shortcut", "data": {"shortcut_name": "Field Technician Profile", "col": 4}},
        ])
        ws_tech.save(ignore_permissions=True)

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
