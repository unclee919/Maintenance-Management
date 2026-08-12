import frappe

@frappe.whitelist()
def run():
    for ws_name in ['Maintenance Management', 'Technician Dashboard']:
        ws = frappe.get_doc('Workspace', ws_name)
        print(f"--- {ws_name} ---")
        print("Public:", ws.public)
        print("Module:", ws.module)
        print("Content:", ws.content)
        print("Shortcuts:", [s.as_dict() for s in ws.get('shortcuts', [])])
        print("Cards:", [c.as_dict() for c in ws.get('cards', [])])
        print("Quick Lists:", [q.as_dict() for q in ws.get('quick_lists', [])])
