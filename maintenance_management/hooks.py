app_name = "maintenance_management"
app_title = "Maintenance Management"
app_publisher = "Manus AI"
app_description = "Field Maintenance Management System for Home Appliances"
app_email = "support@manus.im"
app_license = "mit"

doc_events = {
    "Field Service Request": {
        "before_save": "maintenance_management.doctype.field_service_request.field_service_request.before_save",
        "after_insert": "maintenance_management.doctype.field_service_request.field_service_request.after_insert"
    }
}
