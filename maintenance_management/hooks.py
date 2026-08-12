app_name = "maintenance_management"
app_title = "Maintenance Management"
app_publisher = "Manus AI"
app_description = "Field Maintenance Management System extending ERPNext Sales Order and Sales Invoice"
app_email = "support@manus.im"
app_license = "mit"

doc_events = {
    "Sales Order": {
        "validate": "maintenance_management.controllers.sales_order.validate",
        "before_save": "maintenance_management.controllers.sales_order.before_save",
        "after_insert": "maintenance_management.controllers.sales_order.after_insert",
        "on_update": "maintenance_management.controllers.sales_order.on_update"
    },
    "Sales Invoice": {
        "validate": "maintenance_management.controllers.sales_invoice.validate"
    }
}
