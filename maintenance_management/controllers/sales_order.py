# -*- coding: utf-8 -*-
# Copyright (c) 2026, Manus AI and contributors
# For license information, please see license.txt

import frappe
import requests

def validate(doc, method):
    # Enforce status transition security
    if not doc.is_new():
        old_status = frappe.db.get_value("Sales Order", doc.name, "maintenance_status")
        if old_status and old_status != doc.maintenance_status:
            roles = frappe.get_roles()
            if "System Manager" not in roles and "Administrator" not in roles:
                valid_transitions = {
                    "New": ["Pending Confirmation", "Assigned", "Cancelled"],
                    "Pending Confirmation": ["New", "Assigned", "Cancelled"],
                    "Assigned": ["Accepted", "Cancelled"],
                    "Accepted": ["In Progress", "Cancelled"],
                    "In Progress": ["Waiting for Part", "Waiting for Price Approval", "Completed", "Cancelled"],
                    "Waiting for Part": ["In Progress", "Completed", "Cancelled"],
                    "Waiting for Price Approval": ["In Progress", "Completed", "Cancelled"],
                    "Completed": [],
                    "Cancelled": []
                }
                allowed = valid_transitions.get(old_status, [])
                if doc.maintenance_status not in allowed:
                    frappe.throw(f"Invalid maintenance status transition from '{old_status}' to '{doc.maintenance_status}'. Allowed: {', '.join(allowed) or 'None'}")

def before_save(doc, method):
    try:
        settings = frappe.get_single("Field Maintenance Settings")
        auto_assign = settings.get("auto_assign_technician", 1)
    except Exception:
        auto_assign = 1

    if doc.is_new() and not doc.maintenance_status:
        doc.maintenance_status = "New"
        if auto_assign:
            auto_assign_tech(doc)

def after_insert(doc, method):
    try:
        settings = frappe.get_single("Field Maintenance Settings")
        auto_assign = settings.get("auto_assign_technician", 1)
    except Exception:
        auto_assign = 1

    if doc.maintenance_status == "New" and auto_assign:
        auto_assign_tech(doc)

    trigger_webhook(doc, "Created")

def on_update(doc, method):
    if doc.has_value_changed("maintenance_status"):
        trigger_webhook(doc, f"Status Changed to {doc.maintenance_status}")

        if doc.maintenance_status == "Completed":
            process_erpnext_integration(doc)

def auto_assign_tech(doc):
    tech = frappe.db.get_value("Field Technician", {"status": "Available"}, "name")
    if tech:
        doc.technician = tech
        doc.maintenance_status = "Assigned"

def trigger_webhook(doc, event_type):
    try:
        webhook_url = frappe.db.get_value("Field Maintenance Settings", None, "webhook_url")
        if webhook_url:
            payload = {
                "event": event_type,
                "sales_order": doc.name,
                "customer": doc.customer,
                "status": doc.maintenance_status,
                "equipment_type": doc.equipment_type,
                "technician": doc.technician,
                "grand_total": doc.grand_total
            }
            requests.post(webhook_url, json=payload, timeout=5)
    except Exception as e:
        frappe.log_error(f"Webhook trigger error: {str(e)}", "Maintenance Webhook Error")

def process_erpnext_integration(doc):
    try:
        warehouse = "Stores - EM"
        if doc.technician:
            tech_wh = frappe.db.get_value("Field Technician", doc.technician, "warehouse")
            if tech_wh and frappe.db.exists("Warehouse", tech_wh):
                warehouse = tech_wh

        if not frappe.db.exists("Warehouse", warehouse):
            wh = frappe.db.get_value("Warehouse", {"is_group": 0}, "name")
            if wh:
                warehouse = wh

        # Create Stock Entry (Material Issue) for items consumed in Sales Order
        if frappe.db.exists("DocType", "Stock Entry") and doc.get("items"):
            se_items = []
            for item in doc.get("items"):
                se_items.append({
                    "item_code": item.item_code,
                    "qty": item.qty,
                    "basic_rate": item.rate,
                    "valuation_rate": item.rate,
                    "allow_zero_valuation_rate": 1,
                    "s_warehouse": warehouse
                })
            if se_items:
                se = frappe.get_doc({
                    "doctype": "Stock Entry",
                    "stock_entry_type": "Material Issue",
                    "allow_zero_valuation_rate": 1,
                    "remarks": f"Sales Order Maintenance Service: {doc.name} (Warehouse: {warehouse})",
                    "items": se_items
                })
                se.insert(ignore_permissions=True)
                se.submit()
                frappe.logger().info(f"Created Stock Entry {se.name} for Sales Order {doc.name}")

        # Create Sales Invoice from Sales Order manually
        if frappe.db.exists("DocType", "Sales Invoice"):
            existing_invoice = frappe.db.get_value("Sales Invoice", {"sales_order": doc.name}, "name")
            if not existing_invoice:
                try:
                    inv_items = []
                    for item in doc.get("items") or []:
                        inv_items.append({
                            "item_code": item.item_code,
                            "qty": item.qty,
                            "rate": item.rate,
                            "so_detail": item.name,
                            "sales_order": doc.name,
                            "income_account": "Sales - EM",
                            "cost_center": "Main - EM"
                        })
                    inv = frappe.get_doc({
                        "doctype": "Sales Invoice",
                        "customer": doc.customer,
                        "sales_order": doc.name,
                        "items": inv_items,
                        "docstatus": 1
                    })
                    inv.insert(ignore_permissions=True)
                    frappe.logger().info(f"Created Sales Invoice {inv.name} for Sales Order {doc.name}")
                except Exception as inv_err:
                    import traceback
                    frappe.log_error(f"Sales Invoice Error: {str(inv_err)}\n{traceback.format_exc()}", "Maintenance Sales Invoice Error")
    except Exception as e:
        frappe.log_error(f"ERPNext Integration Error: {str(e)}", "Maintenance ERPNext Error")

@frappe.whitelist()
def run_ai_diagnostics(sales_order_name):
    doc = frappe.get_doc("Sales Order", sales_order_name)
    desc = (doc.issue_description or "").lower()
    suggested_items = []
    est_cost = 100.0

    if "cool" in desc or "ac" in desc or "refrigerant" in desc:
        suggested_items.append({"item_code": "Refrigerant R410A", "qty": 1, "rate": 50.0})
        est_cost = 150.0
    elif "leak" in desc or "water" in desc:
        suggested_items.append({"item_code": "Drain Pipe Valve", "qty": 1, "rate": 25.0})
        est_cost = 80.0
    elif "noise" in desc or "motor" in desc:
        suggested_items.append({"item_code": "Fan Motor Bearing", "qty": 1, "rate": 75.0})
        est_cost = 200.0
    else:
        suggested_items.append({"item_code": "General Diagnostic Kit", "qty": 1, "rate": 40.0})
        est_cost = 90.0

    for p in suggested_items:
        if not frappe.db.exists("Item", p["item_code"]):
            try:
                item_doc = frappe.get_doc({
                    "doctype": "Item",
                    "item_code": p["item_code"],
                    "item_name": p["item_code"],
                    "item_group": "All Item Groups",
                    "stock_uom": "Nos",
                    "valuation_rate": p["rate"],
                    "standard_rate": p["rate"]
                })
                item_doc.insert(ignore_permissions=True)
            except Exception:
                pass

    if not doc.get("items"):
        for p in suggested_items:
            doc.append("items", {
                "item_code": p["item_code"],
                "qty": p["qty"],
                "rate": p["rate"],
                "delivery_date": doc.delivery_date or frappe.utils.nowdate()
            })
        doc.save(ignore_permissions=True)
        return {"status": "success", "message": "AI Diagnostics completed successfully", "estimated_cost": est_cost}

    return {"status": "info", "message": "Items already listed"}
