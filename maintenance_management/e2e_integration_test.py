import frappe
import json
from frappe.utils import nowdate

def run_e2e_integration_test():
    print("=== STARTING E2E INTEGRATION TEST ===")
    
    # 1. IoT Fault Detection Simulation
    print("\n[Step 1] Simulating IoT Fault Detection...")
    from maintenance_management.api import iot_sensor_fault_webhook_with_nearest_dispatch
    
    # Sample fault from HVAC sensor
    iot_res = iot_sensor_fault_webhook_with_nearest_dispatch(
        sensor_id="SNSR-HVAC-99",
        equipment_id="EQ-CHILLER-01",
        fault_code="ERR-PUMP-05",
        reading_value="High Temp",
        latitude=30.0444,
        longitude=31.2357
    )
    
    if iot_res.get("status") != "success":
        print(f"❌ IoT Webhook failed: {iot_res.get('message')}")
        return
    
    so_name = iot_res.get("emergency_order")
    tech_assigned = iot_res.get("nearest_technician")
    print(f"✓ Emergency Sales Order created: {so_name}")
    print(f"✓ Nearest Technician dispatched: {tech_assigned} ({iot_res.get('distance_km')} km)")
    
    # 2. Technician Workflow Simulation
    print("\n[Step 2] Simulating Technician Workflow...")
    so = frappe.get_doc("Sales Order", so_name)
    
    # Transition to Accepted
    so.custom_maintenance_status = "Accepted"
    so.save(ignore_permissions=True)
    print(f"✓ Status transitioned to: {so.custom_maintenance_status}")
    
    # Transition to In Progress
    so.custom_maintenance_status = "In Progress"
    so.save(ignore_permissions=True)
    print(f"✓ Status transitioned to: {so.custom_maintenance_status}")
    
    # 3. Billing & Spare Parts Addition
    print("\n[Step 3] Adding Spare Parts to Billing...")
    from maintenance_management.api import technician_add_billing_items
    
    billing_items = [
        {"item_code": "FILT-003", "qty": 1, "rate": 150}
    ]
    
    bill_res = technician_add_billing_items(so_name, billing_items)
    if bill_res.get("status") != "success":
        print(f"❌ Billing addition failed: {bill_res.get('message')}")
        return
    
    print(f"✓ Spare parts added. New Grand Total: {bill_res.get('grand_total')} EGP")
    
    # 4. Completion Simulation
    print("\n[Step 4] Completing Service Order...")
    so.reload()
    so.custom_maintenance_status = "Completed"
    so.save(ignore_permissions=True)
    print(f"✓ Status transitioned to: {so.custom_maintenance_status}")
    
    # 5. WhatsApp Payment Settlement Link
    print("\n[Step 5] Generating WhatsApp Payment Link...")
    from maintenance_management.api import generate_whatsapp_payment_deep_link
    
    pay_res = generate_whatsapp_payment_deep_link(so_name, so.grand_total)
    if pay_res.get("status") != "success":
        print(f"❌ Payment link generation failed: {pay_res.get('message')}")
        return
    
    print(f"✓ Payment Link Generated: {pay_res.get('payment_deep_link')}")
    print(f"✓ WhatsApp Message: {pay_res.get('message')}")
    
    frappe.db.commit()
    print("\n=== E2E INTEGRATION TEST COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_e2e_integration_test()
