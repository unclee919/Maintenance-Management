import frappe

def verify():
    frappe.init(site="erp.elmrkz.cloud", sites_path="/home/frappe/frappe-bench/sites")
    frappe.connect()
    
    print("Checking Field Maintenance Settings...")
    if frappe.db.exists("Field Maintenance Settings", "Field Maintenance Settings"):
        settings = frappe.get_doc("Field Maintenance Settings", "Field Maintenance Settings")
        print("Settings found successfully:", settings.name)
    else:
        print("Settings record not found, creating default...")
        s = frappe.new_doc("Field Maintenance Settings")
        s.name = "Field Maintenance Settings"
        s.insert(ignore_permissions=True)
        frappe.db.commit()
        print("Created Field Maintenance Settings.")
        
    print("Testing notification trigger...")
    try:
        from maintenance_management.maintenance_management.api import test_technician_notification
        res = test_technician_notification()
        print("Notification test result:", res)
    except Exception as e:
        print("Notification test error:", str(e))

if __name__ == "__main__":
    verify()
