@frappe.whitelist()
def test_settings():
    try:
        doc = frappe.get_doc("Field Maintenance Settings", "Field Maintenance Settings")
        print("SUCCESS LOAD:", doc.name)
        return {"status": "success", "name": doc.name}
    except Exception as e:
        print("ERROR LOAD:", str(e))
        return {"status": "error", "message": str(e)}

def get_sales_order_dashboard(data=None):
    if data is None:
        data = {}
    if isinstance(data, dict):
        if 'transactions' not in data:
            data['transactions'] = []
        # Check if Maintenance section already exists to avoid duplication
        exists = any(t.get('label') == _('Maintenance') for t in data['transactions'])
        if not exists:
            data['transactions'].append({
                'label': _('Maintenance'),
                'items': ['Service Appointment', 'Stock Entry', 'Sales Invoice']
            })
    return data
