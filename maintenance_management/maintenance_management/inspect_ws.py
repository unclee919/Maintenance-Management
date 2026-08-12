import frappe
import json
import random
import string

def random_string(length=10):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))

@frappe.whitelist()
def run():
    # 1. Maintenance Management Workspace
    ws = frappe.get_doc('Workspace', 'Maintenance Management')
    ws.set('shortcuts', [])
    ws.set('links', [])
    
    content = [
        {"id": random_string(), "type": "header", "data": {"text": "Field Maintenance Operations & Analytics", "level": 2}},
        {"id": random_string(), "type": "card", "data": {"card_name": "Open Maintenance Orders", "col": 4}},
        {"id": random_string(), "type": "card", "data": {"card_name": "SLA Breached / Escalated Orders", "col": 4}},
        {"id": random_string(), "type": "card", "data": {"card_name": "Average Customer Rating", "col": 4}},
        {"id": random_string(), "type": "spacer", "data": {"col": 12}},
        {"id": random_string(), "type": "header", "data": {"text": "Core Masters & Settings", "level": 3}},
        {"id": random_string(), "type": "shortcut", "data": {"shortcut_name": "Field Service Request", "col": 3}},
        {"id": random_string(), "type": "shortcut", "data": {"shortcut_name": "Field Technician", "col": 3}},
        {"id": random_string(), "type": "shortcut", "data": {"shortcut_name": "Field Maintenance Settings", "col": 3}}
    ]
    
    ws.content = json.dumps(content)
    ws.public = 1
    
    shortcuts_data = [
        {"label": "Field Service Request", "type": "DocType", "link_to": "Sales Order"},
        {"label": "Field Technician", "type": "DocType", "link_to": "Field Technician"},
        {"label": "Field Maintenance Settings", "type": "DocType", "link_to": "Maintenance Settings"}
    ]
    for s in shortcuts_data:
        ws.append('shortcuts', {
            'label': s["label"],
            'type': s["type"],
            'link_to': s["link_to"],
            'doc_view': 'List',
            'color': 'Grey'
        })
        
    ws.save(ignore_permissions=True)
    
    # 2. Technician Dashboard Workspace
    ws_tech = frappe.get_doc('Workspace', 'Technician Dashboard')
    ws_tech.set('shortcuts', [])
    ws_tech.set('links', [])
    
    content_tech = [
        {"id": random_string(), "type": "header", "data": {"text": "Technician Portal & Field Operations", "level": 2}},
        {"id": random_string(), "type": "shortcut", "data": {"shortcut_name": "Active Service Orders", "col": 4}},
        {"id": random_string(), "type": "shortcut", "data": {"shortcut_name": "Van Warehouse", "col": 4}},
        {"id": random_string(), "type": "shortcut", "data": {"shortcut_name": "Field Technician Profile", "col": 4}}
    ]
    
    ws_tech.content = json.dumps(content_tech)
    ws_tech.public = 1
    
    tech_shortcuts = [
        {"label": "Active Service Orders", "type": "DocType", "link_to": "Sales Order"},
        {"label": "Van Warehouse", "type": "DocType", "link_to": "Warehouse"},
        {"label": "Field Technician Profile", "type": "DocType", "link_to": "Field Technician"}
    ]
    for s in tech_shortcuts:
        ws_tech.append('shortcuts', {
            'label': s["label"],
            'type': s["type"],
            'link_to': s["link_to"],
            'doc_view': 'List',
            'color': 'Blue'
        })
        
    ws_tech.save(ignore_permissions=True)
    
    frappe.db.commit()
    frappe.clear_cache()
    print("Workspaces successfully populated with content blocks.")
