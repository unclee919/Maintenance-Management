import frappe

@frappe.whitelist()
def run():
    ws = frappe.get_doc('Workspace', 'Build')
    print("--- Build Workspace ---")
    print("Content:", ws.content)
    print("Links count:", len(ws.get('links', [])))
    if ws.get('links'):
        print("Sample link:", ws.links[0].as_dict())
    print("Shortcuts count:", len(ws.get('shortcuts', [])))
    if ws.get('shortcuts'):
        print("Sample shortcut:", ws.shortcuts[0].as_dict())
