def get_sales_order_dashboard(data=None):
    if data is None:
        data = {}
    if isinstance(data, dict):
        if 'transactions' not in data:
            data['transactions'] = []
        exists = any(t.get('label') == _('Maintenance') for t in data['transactions'])
        if not exists:
            data['transactions'].append({
                'label': _('Maintenance'),
                'items': ['Service Appointment']
            })
    return data
