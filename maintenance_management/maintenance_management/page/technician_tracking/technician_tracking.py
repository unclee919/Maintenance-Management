
import frappe

@frappe.whitelist()
def get_live_tracking_data():
    """Returns active technicians, their latest GPS locations, and active service orders for the manager map page."""
    technicians = frappe.get_all("Field Technician", fields=["name", "technician_name", "status", "phone", "van_warehouse"])
    orders = frappe.db.sql("""
        select name, customer, custom_assigned_technician, custom_maintenance_status, creation, grand_total 
        from `tabSales Order` 
        where custom_is_maintenance_order = 1 
        and custom_maintenance_status in ['New', 'Assigned', 'On the Way', 'Arrived', 'In Progress']
    """, as_dict=1)
    
    return {
        "technicians": technicians,
        "orders": orders
    }
