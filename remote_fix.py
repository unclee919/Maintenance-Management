import frappe
import json

def run():
    frappe.init(site='erp.elmrkz.cloud', sites_path='sites')
    frappe.connect()

    for ws_name in ['Maintenance Management', 'Technician Dashboard']:
        try:
            ws = frappe.get_doc('Workspace', ws_name)
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
            print("Successfully updated workspace content:", ws_name)
        except Exception as e:
            print("Error updating workspace", ws_name, e)

    frappe.db.commit()
    frappe.clear_cache()
    print("Remote workspace fix completed successfully.")

if __name__ == '__main__':
    run()
