import frappe
from frappe.utils import nowdate, add_days

def populate_data():
    print("=== STARTING SAMPLE DATA POPULATION ===")
    
    # 0. Dependencies
    item_groups = ["Compressors", "Filters", "Valves", "Services"]
    for ig in item_groups:
        if not frappe.db.exists("Item Group", ig):
            frappe.get_doc({"doctype": "Item Group", "item_group_name": ig, "parent_item_group": "All Item Groups"}).insert(ignore_permissions=True)
    
    # 1. Settings
    try:
        if not frappe.db.exists("Field Maintenance Settings"):
            frappe.get_doc({"doctype": "Field Maintenance Settings"}).insert(ignore_permissions=True)
            frappe.db.commit()
            
        settings = frappe.get_doc("Field Maintenance Settings")
        settings.enable_gps_tracking = 1
        settings.auto_assign_technician = 1
        settings.enable_mobile_inventory = 1
        settings.enable_customer_portal = 1
        settings.save(ignore_permissions=True)
        frappe.db.commit()
        print("✓ Settings updated.")
    except Exception as e:
        print(f"⚠ Settings failed: {e}")

    # 2. Items
    items = [
        {"item_code": "SVC-VISIT", "item_name": "Standard Service Visit", "item_group": "Services", "is_stock_item": 0, "standard_rate": 200},
        {"item_code": "COMP-001", "item_name": "Compressor 1.5HP", "item_group": "Compressors", "is_stock_item": 1, "standard_rate": 2500},
        {"item_code": "FILT-003", "item_name": "Refrigerant Filter", "item_group": "Filters", "is_stock_item": 1, "standard_rate": 150}
    ]
    for item in items:
        if not frappe.db.exists("Item", item["item_code"]):
            doc = frappe.get_doc({
                "doctype": "Item",
                "item_code": item["item_code"],
                "item_name": item["item_name"],
                "item_group": item["item_group"],
                "is_stock_item": item["is_stock_item"],
                "stock_uom": "Nos"
            }).insert(ignore_permissions=True)
            frappe.get_doc({
                "doctype": "Item Price",
                "item_code": item["item_code"],
                "price_list": "Standard Selling",
                "price_list_rate": item["standard_rate"]
            }).insert(ignore_permissions=True)
    
    # 3. Technicians
    if not frappe.db.exists("Field Technician", "TECH-001"):
        frappe.get_doc({
            "doctype": "Field Technician",
            "name": "TECH-001",
            "technician_name": "Ahmed Hassan",
            "status": "Available"
        }).insert(ignore_permissions=True)
    
    # 4. Create Multiple Sales Orders
    if not frappe.db.exists("Customer", "Test Customer"):
        frappe.get_doc({"doctype": "Customer", "customer_name": "Test Customer"}).insert(ignore_permissions=True)
        
    for i in range(5):
        so = frappe.new_doc("Sales Order")
        so.customer = "Test Customer"
        so.custom_is_maintenance_order = 1
        so.custom_maintenance_status = "New"
        so.custom_equipment_fault_description = f"Intensive Test Case #{i+1}"
        so.delivery_date = add_days(nowdate(), 1)
        so.append("items", {
            "item_code": "SVC-VISIT",
            "qty": 1,
            "rate": 200,
            "uom": "Nos",
            "conversion_factor": 1.0
        })
        so.insert(ignore_permissions=True)
        so.submit()
        
        # Complete one of them
        if i == 0:
            so.custom_assigned_technician = "TECH-001"
            so.custom_maintenance_status = "Completed"
            so.append("items", {
                "item_code": "FILT-003",
                "qty": 1,
                "rate": 150,
                "uom": "Nos",
                "conversion_factor": 1.0
            })
            so.save(ignore_permissions=True)
            
        print(f"✓ Created SO: {so.name}")

    frappe.db.commit()
    print("=== POPULATION SUCCESSFUL ===")

if __name__ == "__main__":
    populate_data()
