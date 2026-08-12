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

scheduler_events = {
    "daily": [
        "maintenance_management.controllers.sales_order.check_sla_escalations"
    ],
    "hourly": [
        "maintenance_management.controllers.sales_order.check_server_health"
    ]
}

app_include_css = "/assets/maintenance_management/css/mobile_enhancements.css"

after_migrate = "maintenance_management.maintenance_management.api.after_migrate"
