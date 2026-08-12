        for p in suggested_parts:
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
                except Exception as e:
                    frappe.log_error(f"Item creation error: {str(e)}", "AI Diagnostics")
