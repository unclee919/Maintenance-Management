import frappe
from frappe.utils import nowdate, add_days

def populate_data():
    print("=== STARTING SAMPLE DATA POPULATION ===")
    
    # 0. Dependencies
    for ig in ["Compressors", "Filters", "Valves", "Services"]:
        if not frappe.db.exists("Item Group", ig):
            try:
                frappe.get_doc({"doctype": "Item Group", "item_group_name": ig, "parent_item_group": "All Item Groups"}).insert(ignore_permissions=True)
            except: pass
    
    # 1. Settings
    try:
        settings = frappe.get_single("Field Maintenance Settings")
        settings.enable_gps_tracking = 1
        settings.auto_assign_technician = 1
        settings.save(ignore_permissions=True)
        frappe.db.commit()
        print("✓ Settings updated.")
    except Exception as e:
        print(f"⚠ Settings skipped: {e}")

    # 2. Items
    items = [
        {"item_code": "SVC-VISIT", "item_name": "Standard Service Visit", "item_group": "Services", "rate": 200},
        {"item_code": "COMP-001", "item_name": "Compressor 1.5HP", "item_group": "Compressors", "rate": 2500},
        {"item_code": "FILT-003", "item_name": "Refrigerant Filter", "item_group": "Filters", "rate": 150}
    ]
    for item in items:
        if not frappe.db.exists("Item", item["item_code"]):
            try:
                frappe.get_doc({
                    "doctype": "Item",
                    "item_code": item["item_code"],
                    "item_name": item["item_name"],
                    "item_group": item["item_group"],
                    "stock_uom": "Nos"
                }).insert(ignore_permissions=True, ignore_if_duplicate=True)
            except: pass
    
    # 3. Technicians
    if not frappe.db.exists("Field Technician", "Ahmed Hassan"):
        try:
            frappe.get_doc({
                "doctype": "Field Technician",
                "technician_name": "Ahmed Hassan",
                "status": "Available"
            }).insert(ignore_permissions=True, ignore_if_duplicate=True)
        except: pass
    
    # 4. Sales Orders
    if not frappe.db.exists("Customer", "Test Customer"):
        try:
            frappe.get_doc({"doctype": "Customer", "customer_name": "Test Customer"}).insert(ignore_permissions=True)
        except: pass
        
    for i in range(3):
        try:
            so = frappe.new_doc("Sales Order")
            so.customer = "Test Customer"
            so.custom_is_maintenance_order = 1
            so.custom_maintenance_status = "New"
            so.custom_equipment_fault_description = f"Sample maintenance task #{i+1}"
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
            
            if i == 0:
                so.custom_assigned_technician = "Ahmed Hassan"
                so.custom_maintenance_status = "Completed"
                so.save(ignore_permissions=True)
                
            print(f"✓ Created SO: {so.name}")
        except Exception as e:
            print(f"⚠ SO {i} failed: {e}")

    frappe.db.commit()
    print("=== POPULATION COMPLETED ===")

if __name__ == "__main__":
    populate_data()
