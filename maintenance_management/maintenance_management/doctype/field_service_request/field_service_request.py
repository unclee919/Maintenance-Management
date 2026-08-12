            # 2. Create Sales Invoice in ERPNext
            if frappe.db.exists("DocType", "Sales Invoice") and self.total_amount and self.total_amount > 0:
                existing_invoice = frappe.db.get_value("Sales Invoice", {"remarks": ["like", f"%{self.name}%"]}, "name")
                if not existing_invoice:
                    customer = self.customer_name
                    if not frappe.db.exists("Customer", customer):
                        try:
                            cust_doc = frappe.get_doc({
                                "doctype": "Customer",
                                "customer_name": customer,
                                "customer_type": "Individual",
                                "customer_group": "All Customer Groups",
                                "territory": "All Territories"
                            })
                            cust_doc.insert(ignore_permissions=True)
                        except Exception:
                            pass

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
                        "customer": customer,
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
