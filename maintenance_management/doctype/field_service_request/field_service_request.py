# -*- coding: utf-8 -*-
# Copyright (c) 2026, Manus AI and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe.model.document import Document

class FieldServiceRequest(Document):
    def before_save(self):
        try:
            settings = frappe.get_single("Field Maintenance Settings")
            require_human = settings.get("require_human_confirmation", 1)
            auto_assign = settings.get("auto_assign_technician", 1)
        except Exception:
            require_human = 1
            auto_assign = 1
        
        # If new request and human confirmation is required by settings
        if self.is_new():
            if require_human:
                if not self.customer_name or not self.customer_phone or not self.customer_address:
                    self.status = "Pending Correction"
                else:
                    self.status = "Pending Confirmation"
            else:
                self.status = "New"
                if auto_assign:
                    self.auto_assign()

    def after_insert(self):
        try:
            settings = frappe.get_single("Field Maintenance Settings")
            auto_assign = settings.get("auto_assign_technician", 1)
        except Exception:
            auto_assign = 1

        if self.status == "New" and auto_assign:
            self.auto_assign()

        # Send webhook notification (e.g. to n8n workflow or CRM)
        self.trigger_webhook("Created")

    def on_update(self):
        # Trigger webhook on status change
        if self.has_value_changed("status"):
            self.trigger_webhook(f"Status Changed to {self.status}")

            # If completed, trigger ERPNext billing and inventory integration
            if self.status == "Completed":
                self.process_erpnext_integration()

    def auto_assign(self):
        tech = frappe.db.get_value("Field Technician", {"status": "Available", "service_zone": self.customer_address or ""}, "name")
        if not tech:
            tech = frappe.db.get_value("Field Technician", {"status": "Available"}, "name")
        
        if tech:
            self.technician = tech
            self.status = "Assigned"
            self.save(ignore_permissions=True)

    def trigger_webhook(self, event_type):
        try:
            # Check if webhook URL is stored in settings or fetch default n8n endpoint
            webhook_url = frappe.db.get_value("Field Maintenance Settings", None, "webhook_url")
            if webhook_url:
                payload = {
                    "event": event_type,
                    "service_request": self.name,
                    "customer_name": self.customer_name,
                    "customer_phone": self.customer_phone,
                    "status": self.status,
                    "equipment_type": self.equipment_type,
                    "technician": self.technician,
                    "total_amount": self.total_amount
                }
                requests.post(webhook_url, json=payload, timeout=5)
        except Exception as e:
            frapped_msg = f"Webhook trigger error: {str(e)}"
            frappe.log_error(frapped_msg, "Maintenance Webhook Error")

    def process_erpnext_integration(self):
        try:
            # 1. Create Sales Invoice in ERPNext if total_amount > 0 and ERPNext is installed
            if frappe.db.exists("DocType", "Sales Invoice") and self.total_amount and self.total_amount > 0:
                # Check if invoice already created for this request
                existing_invoice = frappe.db.get_value("Sales Invoice", {"custom_service_request": self.name}, "name")
                if not existing_invoice:
                    inv = frappe.get_doc({
                        "doctype": "Sales Invoice",
                        "customer": self.customer_name,
                        "custom_service_request": self.name,
                        "items": [
                            {
                                "item_code": "Maintenance Service",
                                "qty": 1,
                                "rate": self.total_amount,
                                "description": f"Field Service Repair - {self.equipment_type} ({self.name})"
                            }
                        ]
                    })
                    # If Item 'Maintenance Service' doesn't exist, create it or use generic item
                    if not frappe.db.exists("Item", "Maintenance Service"):
                        try:
                            item = frappe.get_doc({
                                "doctype": "Item",
                                "item_code": "Maintenance Service",
                                "item_name": "Maintenance Service",
                                "item_group": "Services",
                                "stock_uom": "Nos"
                            })
                            item.insert(ignore_permissions=True)
                        except Exception:
                            pass
                    
                    inv.insert(ignore_permissions=True)
                    inv.submit()
                    frappe.logger().info(f"Created Sales Invoice {inv.name} for Service Request {self.name}")
        except Exception as e:
            frappe.log_error(f"ERPNext Integration Error: {str(e)}", "Maintenance ERPNext Error")
