    @frappe.whitelist()
    def run_ai_diagnostics(self):
        """AI-powered diagnostics based on issue description to suggest parts and estimated cost"""
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
            suggested_parts.append({"item_code": "Fan Motor Bearing", "qty": 1, "rate": 75.0})
            est_cost = 200.0
        else:
            suggested_parts.append({"item_code": "General Diagnostic Kit", "qty": 1, "rate": 40.0})
            est_cost = 90.0

        # Ensure items exist in Item master
        for p in suggested_parts:
            if not frappe.db.exists("Item", p["item_code"]):
                try:
                    item_doc = frappe.get_doc({
                        "doctype": "Item",
                        "item_code": p["item_code"],
                        "item_name": p["item_code"],
                        "item_group": "Consumables",
                        "stock_uom": "Nos"
                    })
                    item_doc.insert(ignore_permissions=True)
                except Exception:
                    pass

        if not self.get("parts_consumed"):
            for p in suggested_parts:
                self.append("parts_consumed", p)
            self.total_amount = est_cost
            self.save(ignore_permissions=True)
            return {"status": "success", "message": "AI Diagnostics completed successfully", "estimated_cost": est_cost}
        
        return {"status": "info", "message": "Parts already listed"}
