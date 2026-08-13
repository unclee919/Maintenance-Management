import frappe

def run_test():
    frappe.init(site="erp.elmrkz.cloud", sites_path="/home/frappe/frappe-bench/sites")
    frappe.connect()
    
    print("Testing Sales Order creation and technician assignment...")
    
    # Get a customer and item
    customer = frappe.db.get_value("Customer", {}, "name")
    item_code = frappe.db.get_value("Item", {}, "name")
    
    if not customer or not item_code:
        print("No customer or item found in system!")
        return

    so = frappe.new_doc("Sales Order")
    so.customer = customer
    so.delivery_date = frappe.utils.add_days(frappe.utils.nowdate(), 1)
    so.custom_is_maintenance_order = 1
    so.append("items", {
        "item_code": item_code,
        "qty": 1,
        "rate": 100,
        "delivery_date": so.delivery_date
    })
    so.insert(ignore_permissions=True)
    so.submit()
    frappe.db.commit()
    
    print("Sales Order created and submitted:", so.name)
    
    # Check Service Appointment
    sa = frappe.get_all("Service Appointment", filters={"sales_order": so.name}, fields=["name", "technician", "status"])
    print("Created Service Appointments:", sa)

if __name__ == "__main__":
    run_test()
