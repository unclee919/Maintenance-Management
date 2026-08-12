# -*- coding: utf-8 -*-
# Copyright (c) 2026, Manus AI and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe.model.document import Document

class FieldServiceRequest(Document):
    def validate(self):
        total = 0.0
        for part in self.get("parts_consumed") or []:
            if part.rate and part.qty:
                part.amount = part.rate * part.qty
                total += part.amount
        if total > 0 and not self.total_amount:
            self.total_amount = total

    def before_save(self):
        try:
            settings = frappe.get_single("Field Maintenance Settings")
            require_human = settings.get("require_human_confirmation", 1)
            auto_assign = settings.get("auto_assign_technician", 1)
        except Exception:
            require_human = 1
            auto_assign = 1
        
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

        self.trigger_webhook("Created")

    def on_update(self):
        if self.has_value_changed("status"):
            self.trigger_webhook(f"Status Changed to {self.status}")

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
            frappe.log_error(f"Webhook trigger error: {str(e)}", "Maintenance Webhook Error")

    def process_erpnext_integration(self):
        try:
            # 1. Create Stock Entry (Material Issue) for consumed parts
            if frappe.db.exists("DocType", "Stock Entry") and self.get("parts_consumed"):
                se_items = []
                for p in self.get("parts_consumed"):
                    se_items.append({
                        "item_code": p.item_code,
                        "qty": p.qty,
                        "basic_rate": p.rate,
                        "s_warehouse": "Stores - E"
                    })
                if se_items:
                    se = frappe.get_doc({
                        "doctype": "Stock Entry",
                        "stock_entry_type": "Material Issue",
                        "remarks": f"Service Request: {self.name}",
                        "items": se_items
                    })
                    se.insert(ignore_permissions=True)
                    se.submit()
                    frappe.logger().info(f"Created Stock Entry {se.name} for Service Request {self.name}")

            # 2. Create Sales Invoice in ERPNext
            if frappe.db.exists("DocType", "Sales Invoice") and self.total_amount and self.total_amount > 0:
                existing_invoice = frappe.db.get_value("Sales Invoice", {"remarks": ["like", f"%{self.name}%"]}, "name")
                if not existing_invoice:
                    inv_items = []
                    for p in self.get("parts_consumed") or []:
                        inv_items.append({
                            "item_code": p.item_code,
                            "qty": p.qty,
                            "rate": p.rate,
                            "description": f"Part: {p.item_name}"
                        })
                    if not inv_items:
                        inv_items.append({
                            "item_code": "Maintenance Service",
                            "qty": 1,
                            "rate": self.total_amount,
                            "description": f"Field Service Repair - {self.equipment_type} ({self.name})"
                        })

                    inv = frappe.get_doc({
                        "doctype": "Sales Invoice",
                        "customer": self.customer_name,
                        "remarks": f"Service Request: {self.name}",
                        "items": inv_items
                    })
                    
                    if not frappe.db.exists("Item", "Maintenance Service"):
                        try:
                            item = frappe.get_doc({
                                "doctype": "Item",
                                "item_code": "Maintenance Service",
                                "item_name": "Maintenance Service",
                                "item_group": "All Item Groups",
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

    @frappe.whitelist()
    def run_ai_diagnostics(self):
        desc = (self.issue_description or "").lower()
        suggested_parts = []
        est_cost = 100.0

        if "cool" in desc or "ac" in desc or "refrigerant" in desc:
            suggested_parts.append({"item_code": "Refrigerant R410A", "qty": 1, "rate": 50.0})
            est_cost = 150.0
        elif "leak" in desc or "water" in desc:
            suggested_parts.append({"item_code": "Drain Pipe Valve", "qty": 1, "rate": 25.0})
            est_cost = 80.0
        elif "noise" in desc or "motor" in desc:
            suggested_parts.append({"item_code": "Fan Motor Bearing", "Qty": 1, "rate": 75.0})
            est_cost = 200.0
        else:
            suggested_parts.append({"item_code": "General Diagnostic Kit", "qty": 1, "rate": 40.0})
            est_cost = 90.0

        for p in suggested_parts:
            if not frappe.db.exists("Item", p["item_code"]):
                try:
                    item_doc = frappe.get_doc({
                        "doctype": "Item",
                        "item_code": p["item_code"],
                        "item_name": p["item_code"],
                        "item_group": "All Item Groups",
                        "stock_uom": "Nos"
                    })
                    item_doc.insert(ignore_permissions=True)
                except Exception as e:
                    frappe.log_error(f"Item creation error: {str(e)}", "AI Diagnostics Item Error")

        if not self.get("parts_consumed"):
            for p in suggested_parts:
                self.append("parts_consumed", p)
            self.total_amount = est_cost
            self.save(ignore_permissions=True)
            return {"status": "success", "message": "AI Diagnostics completed successfully", "estimated_cost": est_cost}
        
        return {"status": "info", "message": "Parts already listed"}
