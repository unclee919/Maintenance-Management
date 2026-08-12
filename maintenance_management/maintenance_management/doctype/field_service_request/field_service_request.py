            # 1. Create Stock Entry (Material Issue) for consumed parts
            if frappe.db.exists("DocType", "Stock Entry") and self.get("parts_consumed"):
                # First ensure items have stock via Material Receipt
                for p in self.get("parts_consumed"):
                    try:
                        receipt = frappe.get_doc({
                            "doctype": "Stock Entry",
                            "stock_entry_type": "Material Receipt",
                            "to_warehouse": warehouse,
                            "remarks": f"Auto stock receipt for {p.item_code}",
                            "items": [{
                                "item_code": p.item_code,
                                "qty": p.qty,
                                "basic_rate": p.rate,
                                "valuation_rate": p.rate,
                                "t_warehouse": warehouse
                            }]
                        })
                        receipt.insert(ignore_permissions=True)
                        receipt.submit()
                    except Exception:
                        pass

                se_items = []
                for p in self.get("parts_consumed"):
                    se_items.append({
                        "item_code": p.item_code,
                        "qty": p.qty,
                        "basic_rate": p.rate,
                        "valuation_rate": p.rate,
                        "allow_zero_valuation_rate": 1,
                        "s_warehouse": warehouse
                    })
                if se_items:
                    se = frappe.get_doc({
                        "doctype": "Stock Entry",
                        "stock_entry_type": "Material Issue",
                        "allow_zero_valuation_rate": 1,
                        "remarks": f"Service Request: {self.name}",
                        "items": se_items
                    })
                    se.insert(ignore_permissions=True)
                    se.submit()
                    frappe.logger().info(f"Created Stock Entry {se.name} for Service Request {self.name}")
