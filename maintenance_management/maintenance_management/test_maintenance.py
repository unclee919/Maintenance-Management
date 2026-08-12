# -*- coding: utf-8 -*-
import frappedef test_maintenance_workflow():
    print("--- STARTING UNIT TEST SUITE ---")
    
    # 1. Test Customer existence
    cust = frappe.db.get_value("Customer", {}, "name")
    assert cust, "No customer found in system."
    print(f"Verified Customer: {cust}")

    # 2. Test Sales Order Creation & Auto-Assignment
    so = frappe.get_doc({
        "doctype": "Sales Order",
        "customer": cust,
        "delivery_date": frappe.utils.add_days(frappe.utils.nowdate(), 5),
        "equipment_type": "Commercial Chiller Unit",
        "issue_description": "Unit failing to reach target cooling temperature.",
        "maintenance_status": "New",
        "items": [{
            "item_code": "Maintenance Service",
            "qty": 1,
            "rate": 500.0,
            "delivery_date": frappe.utils.add_days(frappe.utils.nowdate(), 5)
        }]
    })
    so.insert(ignore_permissions=True)
    assert so.technician, "Auto-assignment failed: Technician not assigned."
    assert so.maintenance_status == "Assigned", f"Status expected Assigned, got {so.maintenance_status}"
    print(f"Passed: Sales Order {so.name} created and assigned to {so.technician}.")

    # 3. Test AI Diagnostics
    from maintenance_management.controllers.sales_order import run_ai_diagnostics
    diag_res = run_ai_diagnostics(so.name)
    assert diag_res["status"] == "success", "AI Diagnostics failed."
    print(f"Passed: AI Diagnostics returned estimated cost: {diag_res['estimated_cost']}")

    # 4. Test Status Transition Security (Illegal Jump)
    so.reload()
    so.maintenance_status = "New" # Reset to test illegal jump
    so.db_set("maintenance_status", "New")
    
    so.maintenance_status = "Completed"
    try:
        so.save()
        raise AssertionError("Illegal status transition from New to Completed was NOT blocked!")
    except Exception as e:
        if "Invalid maintenance status transition" in str(e):
            print("Passed: Status transition security successfully blocked illegal jump.")
        else:
            raise e

    # 5. Test Valid Lifecycle & Completion
    so.reload()
    so.maintenance_status = "Accepted"
    so.save(ignore_permissions=True)
    so.maintenance_status = "In Progress"
    so.save(ignore_permissions=True)
    so.maintenance_status = "Completed"
    so.feedback_score = "5 - Excellent"
    so.customer_feedback = "Outstanding service and rapid repair."
    so.save(ignore_permissions=True)
    print(f"Passed: Sales Order {so.name} successfully completed and saved.")

    # 6. Test SLA Escalation Job
    from maintenance_management.controllers.sales_order import check_sla_escalations
    check_sla_escalations()
    print("Passed: SLA escalation background check executed successfully.")

    print("--- ALL UNIT TESTS COMPLETED SUCCESSFULLY ---")
