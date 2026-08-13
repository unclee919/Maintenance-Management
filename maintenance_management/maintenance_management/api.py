import frappe
from frappe import _

def test_settings():
    try:
        doc = frappe.get_doc("Field Maintenance Settings", "Field Maintenance Settings")
        print("SUCCESS LOAD:", doc.name)
        return {"status": "success", "name": doc.name}
    except Exception as e:
        print("ERROR LOAD:", str(e))
        return {"status": "error", "message": str(e)}
