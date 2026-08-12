import frappe

def run():
    # 1. Create Print Format safely via Python dict
    if not frappe.db.exists('Print Format', 'Maintenance Service Ticket'):
        pf = frappe.get_doc({
            'doctype': 'Print Format',
            'name': 'Maintenance Service Ticket',
            'doc_type': 'Sales Order',
            'standard': 'No',
            'module': 'Maintenance Management',
            'print_format_type': 'Jinja',
            'html': '<div><h3>Maintenance Service Ticket</h3><p>Order: {{ doc.name }}</p></div>'
        })
        pf.insert(ignore_permissions=True)
        frappe.db.commit()
        print('Print format created successfully.')

    # 2. Create sample data if not exists
    if not frappe.db.exists('Item', 'MAINT-SVC-01'):
        item = frappe.get_doc({
            'doctype': 'Item',
            'item_code': 'MAINT-SVC-01',
            'item_name': 'Standard Maintenance Service',
            'item_group': 'Services',
            'stock_uom': 'Nos',
            'is_stock_item': 0,
            'standard_rate': 150.0
        })
        item.insert(ignore_permissions=True)
        print('Sample Item created.')

    if not frappe.db.exists('Warehouse', 'Van Warehouse - Tech 1'):
        wh = frappe.get_doc({
            'doctype': 'Warehouse',
            'warehouse_name': 'Van Warehouse - Tech 1',
            'company': frappe.defaults.get_defaults().get('company') or frappe.get_all('Company')[0].name
        })
        wh.insert(ignore_permissions=True)
        print('Van Warehouse created.')

    if not frappe.db.exists('Field Technician', 'TECH-001'):
        tech = frappe.get_doc({
            'doctype': 'Field Technician',
            'name': 'TECH-001',
            'employee_name': 'Ahmed Mechanic',
            'status': 'Available',
            'zone': 'North Zone',
            'skill': 'HVAC & Electrical',
            'cell_number': '+966500000000',
            'shift_start': '08:00:00',
            'shift_end': '17:00:00',
            'van_warehouse': 'Van Warehouse - Tech 1',
            'current_latitude': 24.7136,
            'current_longitude': 46.6753
        })
        tech.insert(ignore_permissions=True)
        print('Sample Field Technician created.')

    frappe.db.commit()
    print('Sample data generation completed successfully.')

if __name__ == '__main__':
    frappe.connect(site='erp.elmrkz.cloud')
    run()
