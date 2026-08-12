import frappe
import json

def fix():
    for ws_name in ['Maintenance Management', 'Technician Dashboard']:
        try:
            ws = frappe.get_doc('Workspace', ws_name)
            print(f"Workspace {ws_name} current content:", ws.content)
            
            if ws_name == 'Maintenance Management':
                content_blocks = [
                    {"type": "header", "data": {"text": "Field Maintenance Operations", "level": 2}},
                    {"type": "shortcut", "data": {"shortcut_name": "Field Service Request"}},
                    {"type": "shortcut", "data": {"shortcut_name": "Field Technician"}},
                    {"type": "shortcut", "data": {"shortcut_name": "Field Maintenance Settings"}}
                ]
            else:
                content_blocks = [
                    {"type": "header", "data": {"text": "Technician Portal & Field Operations", "level": 2}},
                    {"type": "shortcut", "data": {"shortcut_name": "Field Service Request"}}
                ]
                
            ws.content = json.dumps(content_blocks)
            ws.public = 1
            ws.save(ignore_permissions=True)
            print(f"Successfully updated content for {ws_name}")
        except Exception as e:
            print(f"Error updating {ws_name}: {e}")

    frappe.db.commit()
    frappe.clear_cache()
    print("Workspace fix completed.")

if __name__ == '__main__':
    fix()
