app_name = "maintenance_management"
app_title = "Maintenance Management"
app_publisher = "Enterprise Maintenance Solutions"
app_description = "Field Maintenance Management System extending ERPNext Sales Order and Sales Invoice"
app_email = "support@elmrkz.cloud"
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

permission_query_conditions = {
    "Sales Order": "maintenance_management.maintenance_management.api.sales_order_permission_query"
}

scheduler_events = {
    "daily": [
        "maintenance_management.controllers.sales_order.check_sla_escalations",
        "maintenance_management.maintenance_management.doctype.amc_contract.amc_contract.generate_amc_service_requests",
        "maintenance_management.maintenance_management.api.send_automated_daily_utilization_report"
    ],
    "hourly": [
        "maintenance_management.controllers.sales_order.check_server_health"
    ]
}

app_include_css = "/assets/maintenance_management/css/mobile_enhancements.css"

after_migrate = "maintenance_management.maintenance_management.api.after_migrate"
