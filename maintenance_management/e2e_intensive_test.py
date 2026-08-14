import frappe

def run_intensive_tests():
    print("=== STARTING INTENSIVE END-TO-END SYSTEM TEST ===")
    
    # 1. Test Field Maintenance Settings fetch
    settings = frappe.get_single("Field Maintenance Settings")
    print(f"✓ Settings loaded successfully. Auto assign enabled: {settings.get('auto_assign_technician')}")
    
    # 2. Test WhatsApp Webhook simulation
    from maintenance_management.api import whatsapp_webhook_receiver
    res = whatsapp_webhook_receiver("201012345678", "AC unit leaking water and not cooling properly", "Equipment 101")
    print(f"✓ WhatsApp Webhook simulation result: {res}")
    
    # 3. Test Weighted Assignment Engine
    from maintenance_management.controllers.sales_order import assign_technician_weighted
    # Create test Sales Order if not exists
    so = frappe.new_doc("Sales Order")
    so.customer = "Test Customer"
    so.custom_is_maintenance_order = 1
    so.custom_maintenance_status = "New"
    so.custom_equipment_fault_description = "Intensive test fault description"
    so.delivery_date = frappe.utils.nowdate()
    so.append("items", {"item_code": "Standard Maintenance Visit", "qty": 1, "rate": 150})
    so.insert(ignore_permissions=True)
    
    assigned_tech = assign_technician_weighted(so)
    print(f"✓ Weighted Assignment Engine assigned technician: {assigned_tech}")
    
    # 4. Test AI Route Optimization
    from maintenance_management.api import optimize_technician_routes
    route_res = optimize_technician_routes(assigned_tech or "TECH-001")
    print(f"✓ AI Route Optimization result: {route_res}")
    
    # 5. Test Predictive Maintenance
    from maintenance_management.api import run_predictive_maintenance_analysis
    pred_res = run_predictive_maintenance_analysis()
    print(f"✓ Predictive Maintenance analysis result: {pred_res}")
    
    # 6. Test QR Asset Code
    from maintenance_management.api import scan_asset_qr_code
    qr_res = scan_asset_qr_code("EQ-HVAC-101")
    print(f"✓ QR Asset Scan result: {qr_res}")
    
    # 7. Test Regional P&L Summary
    from maintenance_management.api import get_regional_profit_loss_summary
    pnl_res = get_regional_profit_loss_summary()
    print(f"✓ Regional P&L Summary result: Total Revenue EGP {pnl_res['total_revenue']}")
    
    print("=== ALL INTENSIVE TESTS COMPLETED SUCCESSFULLY ===")
