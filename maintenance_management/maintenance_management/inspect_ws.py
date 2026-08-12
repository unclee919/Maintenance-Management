import frappe
import json
import random
import string

def random_string(length=10):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))

@frappe.whitelist()
def run():
    for ws_name in ['Maintenance Management', 'Technician Dashboard']:
        ws = frappe.get_doc('Workspace', ws_name)
        
        # Clear existing shortcuts and links
        ws.set('shortcuts', [])
        ws.set('links', [])
        
        content_blocks = []
        
        if ws_name == 'Maintenance Management':
            content_blocks.append({"id": random_string(), "type": "header", "data": {"text": "Field Maintenance Operations", "level": 2}})
            
            # Add shortcuts
            shortcuts_data = [
                {"label": "Field Service Request", "type": "DocType", "link_to": "Sales Order"},
                {"label": "Field Technician", "type": "DocType", "link_to": "Field Technician"},
                {"label": "Field Maintenance Settings", "type": "DocType", "link_to": "Maintenance Settings"}
            ]
            for s in shortcuts_data:
                sc_id = random_string()
                content_blocks.append({"id": sc_id, "type": "shortcut", "data": {"shortcut_name": s["label"], "col": 3}})
                ws.append('shortcuts', {
                    'label': s["label"],
                    'type': s["type"],
                    'link_to': s["link_to"],
                    'doc_view': 'List',
                    'color': 'Grey'
                })
        else:
            content_blocks.append({"id": random_string(), "type": "header", "data": {"text": "Technician Portal & Field Operations", "level": 2}})
            shortcuts_data = [
                {"label": "Field Service Request", "type": "DocType", "link_to": "Sales Order"}
            ]
            for s in shortcuts_data:
                sc_id = random_string()
                content_blocks.append({"id": sc_id, "type": "shortcut", "data": {"shortcut_name": s["label"], "col": 3}})
                ws.append('shortcuts', {
                    'label': s["label"],
                    'type': s["type"],
                    'link_to': s["link_to"],
                    'doc_view': 'List',
                    'color': 'Grey'
                })
                
        ws.content = json.dumps(content_blocks)
        ws.public = 1
        ws.save(ignore_permissions=True)
        print(f"Successfully reconstructed workspace: {ws_name}")
        
    frappe.db.commit()
    frappe.clear_cache()
    print("All workspaces reconstructed and cache cleared.")
