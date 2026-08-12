# -*- coding: utf-8 -*-
# Copyright (c) 2026, Manus AI and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ServiceRequest(Document):
    def before_save(self):
        settings = frappe.get_single("Maintenance Settings")
        
        # If new request and human confirmation is required by settings
        if self.is_new():
            if settings.get("require_human_confirmation"):
                # Check if basic data is missing
                if not self.customer_name or not self.customer_phone or not self.customer_address:
                    self.status = "Pending Correction"
                else:
                    self.status = "Pending Confirmation"
            else:
                self.status = "New"
                if settings.get("auto_assign_technician"):
                    self.auto_assign()

    def after_insert(self):
        settings = frappe.get_single("Maintenance Settings")
        if self.status == "New" and settings.get("auto_assign_technician"):
            self.auto_assign()

    def auto_assign(self):
        # Simple smart dispatch based on service zone or first available technician
        tech = frappe.db.get_value("Technician", {"status": "Available", "service_zone": self.customer_address or ""}, "name")
        if not tech:
            # Fallback to any available technician
            tech = frappe.db.get_value("Technician", {"status": "Available"}, "name")
        
        if tech:
            self.technician = tech
            self.status = "Assigned"
            self.save(ignore_permissions=True)
