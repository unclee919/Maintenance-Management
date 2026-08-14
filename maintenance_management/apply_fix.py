import frappe
import json

def execute():
    if frappe.db.exists('Workspace', 'Maintenance Management'):
        ws = frappe.get_doc('Workspace', 'Maintenance Management')
        ws.content = json.dumps([
            {"id": "hdr1", "type": "header", "data": {"text": "Field Maintenance Operations", "col": 12}},
            {"id": "sc1", "type": "shortcut", "data": {"shortcut_name": "Service Request", "col": 3}},
            {"id": "sc2", "type": "shortcut", "data": {"shortcut_name": "Sales Order", "col": 3}},
            {"id": "sc3", "type": "shortcut", "data": {"shortcut_name": "Field Technician", "col": 3}},
            {"id": "sc4", "type": "shortcut", "data": {"shortcut_name": "Field Maintenance Settings", "col": 3}}
        ])
        ws.category = 'Modules'
        ws.public = 1
        ws.is_hidden = 0
        ws.parent_page = ''
        ws.save(ignore_permissions=True)
        print("Maintenance Management workspace fixed.")

    if frappe.db.exists('Workspace', 'Technician Dashboard'):
        td = frappe.get_doc('Workspace', 'Technician Dashboard')
        td.content = json.dumps([
            {"id": "thdr1", "type": "header", "data": {"text": "Technician Portal & Field Operations", "col": 12}},
            {"id": "tsc1", "type": "shortcut", "data": {"shortcut_name": "Service Request", "col": 4}},
            {"id": "tsc2", "type": "shortcut", "data": {"shortcut_name": "Sales Order", "col": 4}}
        ])
        td.category = 'Modules'
        td.public = 1
        td.is_hidden = 0
        td.parent_page = ''
        td.save(ignore_permissions=True)
        print("Technician Dashboard workspace fixed.")

    frappe.db.commit()
    print("ALL FIXES COMMITTED")
