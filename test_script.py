import traceback
import frappe

try:
    doc = frappe.get_doc({
        "doctype": "Field Service Request",
        "customer_name": "Jessica Alba",
        "customer_phone": "+1777888999",
        "customer_address": "Zone C",
        "equipment_type": "Air Conditioner",
        "issue_description": "AC unit not cooling and leaking refrigerant gas"
    })
    doc.insert(ignore_permissions=True)
    print("Created Request:", doc.name)
    
    # Run AI Diagnostics
    doc.run_ai_diagnostics()
    print("Parts consumed:", len(doc.get("parts_consumed") or []))
    print("Total amount:", doc.total_amount)
    
    # Complete
    doc.status = "Completed"
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    print("Request status set to Completed successfully!")
    
    # Check Stock Entry
    se_list = frappe.get_all("Stock Entry", filters={"remarks": ["like", f"%{doc.name}%"]}, fields=["name"])
    print("Generated Stock Entries:", se_list)
    
    # Check Sales Invoice
    si_list = frappe.get_all("Sales Invoice", filters={"remarks": ["like", f"%{doc.name}%"]}, fields=["name"])
    print("Generated Sales Invoices:", si_list)
    
except Exception:
    traceback.print_exc()
