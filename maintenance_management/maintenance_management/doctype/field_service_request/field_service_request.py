# -*- coding: utf-8 -*-
# Copyright (c) 2026, Manus AI and contributors
# For license information, please see license.txt

import frappe
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

    def auto_assign(self):
        tech = frappe.db.get_value("Field Technician", {"status": "Available", "service_zone": self.customer_address or ""}, "name")
        if not tech:
            tech = frappe.db.get_value("Field Technician", {"status": "Available"}, "name")
        
        if tech:
            self.technician = tech
            self.status = "Assigned"
            self.save(ignore_permissions=True)
