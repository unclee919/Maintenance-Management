import frappe
from frappe.utils import nowdate, add_days

def populate_data():
    print("=== STARTING SAMPLE DATA POPULATION ===")
    
    # 0. Ensure Dependencies Exist
    item_groups = ["Compressors", "Filters", "Valves", "Services"]
    for ig in item_groups:
        if not frappe.db.exists("Item Group", ig):
            frappe.get_doc({"doctype": "Item Group", "item_group_name": ig, "parent_item_group": "All Item Groups"}).insert(ignore_permissions=True)
    
    # 1. Update Field Maintenance Settings
    if not frappe.db.exists("Field Maintenance Settings"):
        frappe.get_doc({"doctype": "Field Maintenance Settings"}).insert(ignore_permissions=True)
        frappe.db.commit()
        
    try:
        settings = frappe.get_doc("Field Maintenance Settings")
        settings.enable_gps_tracking = 1
        settings.require_human_confirmation = 0
        settings.enable_price_approval = 1
        settings.enable_mobile_inventory = 1
        settings.enable_customer_portal = 1
        settings.auto_assign_technician = 1
        settings.default_warranty_days = 90
        settings.enable_monthly_report = 1
        settings.monthly_report_email = "admin@elmrkz.cloud"
        settings.response_time_threshold_mins = 20
        settings.alert_email_recipients = "alerts@elmrkz.cloud"
        settings.enable_weekly_report = 1
        settings.weekly_report_email = "management@elmrkz.cloud"
        settings.send_weekly_report_to_whatsapp = 1
        settings.whatsapp_report_group_id = "201012345678-group"
        settings.enable_online_payment_link = 1
        settings.payment_gateway_url = "https://pay.elmrkz.cloud/pay"
        settings.enable_low_stock_alerts = 1
        settings.low_stock_threshold_qty = 5
        settings.enable_auto_reorder = 1
        settings.reorder_qty = 20
        settings.enable_forecast_auto_po = 1
        settings.enable_daily_utilization_report = 1
        settings.utilization_report_email = "supervisors@elmrkz.cloud"
        settings.enable_price_alert = 1
        settings.price_alert_threshold_pct = 10.0
        settings.enable_fallback_supplier = 1
        settings.save(ignore_permissions=True)
        frappe.db.commit()
        print("✓ Field Maintenance Settings updated.")
    except Exception as e:
        print(f"⚠ Settings update failed: {e}")

    # 2. Create Items (Spare Parts & Services)
    items = [
        {"item_code": "SVC-VISIT", "item_name": "Standard Service Visit", "item_group": "Services", "is_stock_item": 0, "standard_rate": 200},
        {"item_code": "COMP-001", "item_name": "Compressor 1.5HP", "item_group": "Compressors", "is_stock_item": 1, "standard_rate": 2500},
        {"item_code": "FILT-003", "item_name": "Refrigerant Filter", "item_group": "Filters", "is_stock_item": 1, "standard_rate": 150},
        {"item_code": "VALVE-002", "item_name": "Expansion Valve", "item_group": "Valves", "is_stock_item": 1, "standard_rate": 450}
    ]
    for item in items:
        try:
            if not frappe.db.exists("Item", item["item_code"]):
                doc = frappe.get_doc({
                    "doctype": "Item",
                    "item_code": item["item_code"],
                    "item_name": item["item_name"],
                    "item_group": item["item_group"],
                    "is_stock_item": item["is_stock_item"],
                    "stock_uom": "Nos"
                })
                doc.insert(ignore_permissions=True)
                # Add Price
                frappe.get_doc({
                    "doctype": "Item Price",
                    "item_code": item["item_code"],
                    "price_list": "Standard Selling",
                    "price_list_rate": item["standard_rate"]
                }).insert(ignore_permissions=True)
        except Exception as e:
            print(f"⚠ Item {item['item_code']} creation failed: {e}")
    print("✓ Maintenance Items processed.")

    # 3. Create Field Technicians
    techs = [
        {"name": "TECH-001", "technician_name": "Ahmed Hassan", "status": "Available", "current_latitude": 30.0444, "current_longitude": 31.2357},
        {"name": "TECH-002", "technician_name": "Mohamed Ali", "status": "Busy", "current_latitude": 30.0666, "current_longitude": 31.2557}
    ]
    for t in techs:
        try:
            if not frappe.db.exists("Field Technician", t["name"]):
                frappe.get_doc({
                    "doctype": "Field Technician",
                    "name": t["name"],
                    "technician_name": t["technician_name"],
                    "status": t["status"],
                    "current_latitude": t["current_latitude"],
                    "current_longitude": t["current_longitude"]
                }).insert(ignore_permissions=True)
        except Exception as e:
            print(f"⚠ Technician {t['name']} creation failed: {e}")
    print("✓ Field Technicians processed.")

    # 4. Create Sample Sales Orders (Maintenance Requests)
    try:
        if not frappe.db.exists("Customer", "Test Customer"):
            frappe.get_doc({"doctype": "Customer", "customer_name": "Test Customer"}).insert(ignore_permissions=True)
            
        for i in range(1, 4):
            so = frappe.new_doc("Sales Order")
            so.customer = "Test Customer"
            so.custom_is_maintenance_order = 1
            so.custom_maintenance_status = "New" if i == 1 else ("Assigned" if i == 2 else "Completed")
            so.custom_equipment_fault_description = f"Sample fault report {i}: AC not cooling."
            so.delivery_date = add_days(nowdate(), 1)
            so.append("items", {"item_code": "SVC-VISIT", "qty": 1, "rate": 200})
            
            if i >= 2:
                so.custom_assigned_technician = "TECH-001"
                
            if i == 3:
                so.custom_maintenance_status = "Completed"
                if frappe.db.exists("Item", "FILT-003"):
                    so.append("items", {"item_code": "FILT-003", "qty": 1, "rate": 150})
                
            so.insert(ignore_permissions=True)
            so.submit()
            print(f"✓ Sales Order {so.name} created (Status: {so.custom_maintenance_status})")
    except Exception as e:
        print(f"⚠ Sales Order creation failed: {e}")

    frappe.db.commit()
    print("=== SAMPLE DATA POPULATION COMPLETED ===")

if __name__ == "__main__":
    populate_data()
