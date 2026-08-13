@frappe.whitelist()
def test_accept_reject_workflow():
    """Tests technician accept and reject workflow on latest maintenance sales order."""
    sos = frappe.get_all("Sales Order", filters={"custom_is_maintenance_order": 1}, order_by="creation desc", limit=1)
    if not sos:
        return {"status": "error", "message": "No maintenance sales order found for testing."}
    so_name = sos[0].name
    
    sa_list = frappe.get_all("Service Appointment", filters={"sales_order": so_name}, limit=1)
    if not sa_list:
        from maintenance_management.controllers.sales_order import create_service_appointment
        so_doc = frappe.get_doc("Sales Order", so_name)
        create_service_appointment(so_doc)
        sa_list = frappe.get_all("Service Appointment", filters={"sales_order": so_name}, limit=1)
        
    sa_name = sa_list[0].name if sa_list else so_name
        
    from maintenance_management.controllers.sales_order import accept_dispatch, reject_dispatch
    accept_res = accept_dispatch(sa_name)
    status_after_accept = frappe.db.get_value("Sales Order", so_name, "custom_maintenance_status")
    
    reject_res = reject_dispatch(sa_name, reason="Automated test schedule conflict")
    status_after_reject = frappe.db.get_value("Sales Order", so_name, "custom_maintenance_status")
    
    return {
        "status": "success",
        "sales_order": so_name,
        "service_appointment": sa_name,
        "accept_result": accept_res,
        "status_after_accept": status_after_accept,
        "reject_result": reject_res,
        "status_after_reject": status_after_reject
    }
