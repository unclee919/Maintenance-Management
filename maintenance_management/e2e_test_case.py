import traceback
import frappe

frappe.init("erp.elmrkz.cloud")
frappe.connect()

try:
    print("=== STEP 1: Ensuring Technician Exists ===")
    tech_name = "Tech-Alex-01"
    if not frappe.db.exists("Field Technician", tech_name):
        tech = frappe.get_doc({
            "doctype": "Field Technician",
            "technician_name": "Alex Turner",
            "phone": "+1987654321",
            "service_zone": "Zone A",
            "status": "Available"
        })
        tech.insert(ignore_permissions=True)
        print(f"Created Technician: {tech.name}")
    else:
        print(f"Technician already exists: {tech_name}")

    print("\n=== STEP 2: Generating Sample Order (Service Request) ===")
    doc = frappe.get_doc({
        "doctype": "Field Service Request",
        "customer_name": "Sarah Connor",
        "customer_phone": "+1122334455",
        "customer_address": "Zone A",
        "equipment_type": "Commercial Chiller",
        "issue_description": "Chiller unit compressor overheating and making loud rattling noise"
    })
    doc.insert(ignore_permissions=True)
    print(f"Successfully generated Service Request: {doc.name}")
    print(f"Initial Status: {doc.status}")

    print("\n=== STEP 3: Assigning Technician ===")
    doc.technician = tech_name
    doc.status = "Assigned"
    doc.save(ignore_permissions=True)
    print(f"Assigned Technician {tech_name} to {doc.name}. Current Status: {doc.status}")

    print("\n=== STEP 4: Simulating Technician Process (Accepted -> In Progress -> AI Diagnostics) ===")
    doc.status = "Accepted"
    doc.save(ignore_permissions=True)
    print(f"Technician accepted request. Status: {doc.status}")

    doc.status = "In Progress"
    doc.save(ignore_permissions=True)
    print(f"Work started. Status: {doc.status}")

    # Run AI Diagnostics to auto-recommend parts and pricing
    diag_res = doc.run_ai_diagnostics()
    print("AI Diagnostics Result:", diag_res)
    print(f"Parts Consumed Count: {len(doc.get('parts_consumed') or [])}")
    for p in doc.get("parts_consumed") or []:
        print(f" - Part: {p.item_code}, Qty: {p.qty}, Rate: {p.rate}, Amount: {p.amount}")
    print(f"Total Amount: {doc.total_amount}")

    print("\n=== STEP 5: Finishing Task (Marking as Completed & ERPNext Integration) ===")
    doc.status = "Completed"
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    print(f"Task finished! Final Status: {doc.status}")

    # Verify generated records in ERPNext
    se_list = frappe.get_all("Stock Entry", filters={"remarks": ["like", f"%{doc.name}%"]}, fields=["name", "stock_entry_type"])
    print(f"Generated Stock Entries: {se_list}")

    si_list = frappe.get_all("Sales Invoice", filters={"remarks": ["like", f"%{doc.name}%"]}, fields=["name", "grand_total"])
    print(f"Generated Sales Invoices: {si_list}")

    print("\n=== TEST CASE COMPLETED SUCCESSFULLY ===")
except Exception:
    traceback.print_exc()
finally:
    frappe.destroy()
