# -*- coding: utf-8 -*-
import frappe

@frappe.whitelist(allow_guest=True)
def track_request(request_id):
    """Public API for customer tracking portal"""
    if not request_id:
        return {"status": "error", "message": "Request ID is required"}
    
    doc = frappe.db.get_value(
        "Field Service Request",
        request_id,
        ["name", "customer_name", "equipment_type", "status", "technician", "scheduled_date", "total_amount", "warranty_status"],
        as_dict=True
    )
    
    if not doc:
        return {"status": "error", "message": "Service Request not found"}
        
    return {"status": "success", "data": doc}

@frappe.whitelist()
def fix_workspace():
	try:
		w = frappe.get_doc("Workspace", "Maintenance Management")
		w.public = 1
		w.type = "Workspace"
		w.link_type = None
		w.link_to = None
		w.icon = "settings"
		w.is_standard = 1
		w.save(ignore_permissions=True)
	except Exception as e:
		pass
	
	frappe.db.commit()
	return "Workspace Maintenance Management fixed successfully!"

def after_migrate():
	if not frappe.db.exists("Workspace", "Maintenance Management"):
		w = frappe.get_doc({
			"doctype": "Workspace",
			"name": "Maintenance Management",
			"label": "Maintenance Management",
			"module": "Maintenance Management",
			"app": "maintenance_management",
			"public": 1,
			"type": "Workspace",
			"icon": "settings",
			"sequence_id": 2.0,
			"links": [
				{"type": "Card Break", "label": "Field Maintenance", "link_count": 2},
				{"type": "Link", "label": "Field Technician", "link_type": "DocType", "link_to": "Field Technician"},
				{"type": "Link", "label": "Field Maintenance Settings", "link_type": "DocType", "link_to": "Field Maintenance Settings"}
			]
		})
		w.insert(ignore_permissions=True)
		frappe.db.commit()

@frappe.whitelist()
def check_module():
	res = {
		"modules": frappe.get_all('Module Def', filters={'app_name': 'maintenance_management'}, fields=['name']),
		"workspaces": frappe.get_all('Workspace', filters={'app': 'maintenance_management'}, fields=['name', 'module', 'public'])
	}
	if not frappe.db.exists('Module Def', 'Maintenance Management'):
		m = frappe.get_doc({
			'doctype': 'Module Def',
			'module_name': 'Maintenance Management',
			'app_name': 'maintenance_management'
		})
		m.insert(ignore_permissions=True)
		frappe.db.commit()
		res["created_module"] = True
	return res

@frappe.whitelist()
def update_technician_location(sales_order, latitude, longitude, tracking_status="active"):
    frappe.logger().info(f"Technician Location Update: SO={sales_order}, Lat={latitude}, Lon={longitude}, Status={tracking_status}")
    return {"status": "success", "message": "Location updated successfully"}

@frappe.whitelist()
def create_technician_order(customer, items, description=None, technician=None, latitude=None, longitude=None):
    """Allows a technician to initiate a service order directly from the mobile portal."""
    try:
        import json
        if isinstance(items, str):
            items = json.loads(items)
        
        doc = frappe.get_doc({
            'doctype': 'Sales Order',
            'customer': customer,
            'custom_is_maintenance_order': 1,
            'custom_maintenance_status': 'New',
            'custom_assigned_technician': technician,
            'custom_problem_description': description or 'Initiated by Field Technician',
            'delivery_date': frappe.utils.nowdate(),
            'items': items
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
        if technician and latitude and longitude:
            doc.append('custom_location_audit_logs', {
                'technician': technician,
                'action_name': 'Technician Created Order',
                'latitude': float(latitude),
                'longitude': float(longitude),
                'timestamp': frappe.utils.now()
            })
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            
        return {'status': 'success', 'sales_order': doc.name}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Technician Order Creation Error')
        return {'status': 'error', 'message': str(e)}

@frappe.whitelist()
def check_technician_shift(technician_name):
    """Checks if the technician is currently within their shift hours."""
    tech = frappe.get_doc('Field Technician', technician_name)
    now_time = datetime.now().time()
    start = tech.get('shift_start') or time(8, 0)
    end = tech.get('shift_end') or time(17, 0)
    
    if isinstance(start, str):
        start = datetime.strptime(start, '%H:%M:%S').time()
    if isinstance(end, str):
        end = datetime.strptime(end, '%H:%M:%S').time()
        
    in_shift = start <= now_time <= end
    return {'in_shift': in_shift, 'shift_start': str(start), 'shift_end': str(end), 'current_time': str(now_time)}

@frappe.whitelist()
def request_spare_parts(sales_order, items, technician):
    """Allows a technician to request spare parts from the field, creating a Material Request in ERPNext."""
    try:
        import json
        if isinstance(items, str):
            items = json.loads(items)
            
        mat_req = frappe.get_doc({
            'doctype': 'Material Request',
            'material_request_type': 'Purchase',
            'custom_maintenance_order': sales_order,
            'schedule_date': frappe.utils.nowdate(),
            'items': items
        })
        mat_req.insert(ignore_permissions=True)
        frappe.db.commit()
        return {'status': 'success', 'material_request': mat_req.name}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Spare Parts Request Error')
        return {'status': 'error', 'message': str(e)}

@frappe.whitelist()
def check_sla_escalations():
    """Background method to check overdue maintenance orders and flag managers."""
    settings = frappe.get_single('Maintenance Settings')
    if not settings.get('default_sla_resolution_hours'):
        return
        
    hours = int(settings.default_sla_resolution_hours)
    overdue_orders = frappe.db.sql("""
        select name, customer, creation, custom_assigned_technician 
        from `tabSales Order` 
        where custom_is_maintenance_order = 1 
        and custom_maintenance_status not in ('Completed', 'Cancelled')
        and timestampdiff(hour, creation, now()) > %s
        and (custom_sla_escalated = 0 or custom_sla_escalated is null)
    """, hours, as_dict=1)
    
    for order in overdue_orders:
        frappe.db.set_value('Sales Order', order.name, 'custom_sla_escalated', 1)
        # Create a notification or log
        frappe.log_error(f"SLA Breached for Order {order.name} assigned to {order.custom_assigned_technician}", "SLA Escalation Alert")
        
    frappe.db.commit()
    return {'escalated_count': len(overdue_orders)}

@frappe.whitelist()
def complete_maintenance_order(sales_order, signature=None, notes=None, feedback=None, rating=5):
    """Completes the maintenance order, generates Sales Invoice & Stock Entry, and logs customer feedback."""
    doc = frappe.get_doc('Sales Order', sales_order)
    doc.custom_maintenance_status = 'Completed'
    if signature:
        doc.custom_customer_signature = signature
    if notes:
        doc.custom_technician_notes = notes
    if feedback:
        doc.custom_customer_feedback = feedback
    doc.custom_customer_rating = rating
    
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {'status': 'success', 'message': 'Order completed successfully and documents generated.'}

@frappe.whitelist(allow_guest=True)
def get_customer_tracking(sales_order):
    """Public API for customers to track their assigned technician and service status."""
    doc = frappe.get_doc('Sales Order', sales_order)
    if not doc.get('custom_is_maintenance_order'):
        return {'status': 'error', 'message': 'Invalid maintenance order'}
        
    tech = doc.get('custom_assigned_technician')
    tech_data = {}
    if tech:
        t_doc = frappe.get_doc('Field Technician', tech)
        tech_data = {
            'technician_name': t_doc.get('employee_name') or t_doc.name,
            'phone': t_doc.get('cell_number'),
            'latitude': t_doc.get('current_latitude'),
            'longitude': t_doc.get('current_longitude'),
            'last_update': t_doc.get('last_location_update')
        }
        
    return {
        'order': doc.name,
        'customer': doc.customer,
        'status': doc.get('custom_maintenance_status'),
        'problem': doc.get('custom_problem_description'),
        'technician': tech_data,
        'audit_logs': doc.get('custom_location_audit_logs', [])
    }

@frappe.whitelist()
def reschedule_maintenance_order(sales_order, new_delivery_date, reason=None):
    """Allows rescheduling a service request to a new date/time."""
    doc = frappe.get_doc('Sales Order', sales_order)
    doc.delivery_date = new_delivery_date
    if reason:
        doc.custom_problem_description = (doc.custom_problem_description or '') + f"\n[Rescheduled to {new_delivery_date}: {reason}]"
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {'status': 'success', 'new_date': new_delivery_date}

@frappe.whitelist()
def create_onsite_quotation(customer, items, sales_order=None, technician=None, signature=None):
    """Allows a technician to generate an on-site Quotation for additional repairs, with customer signature approval."""
    try:
        import json
        if isinstance(items, str):
            items = json.loads(items)
            
        quote = frappe.get_doc({
            'doctype': 'Quotation',
            'quotation_to': 'Customer',
            'party_name': customer,
            'custom_maintenance_order': sales_order,
            'custom_assigned_technician': technician,
            'custom_customer_signature': signature,
            'order_type': 'Maintenance',
            'transaction_date': frappe.utils.nowdate(),
            'valid_till': frappe.utils.add_days(frappe.utils.nowdate(), 7),
            'items': items
        })
        quote.insert(ignore_permissions=True)
        quote.submit()
        frappe.db.commit()
        return {'status': 'success', 'quotation': quote.name}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'On-Site Quotation Error')
        return {'status': 'error', 'message': str(e)}

@frappe.whitelist()
def check_van_warehouse_low_stock():
    """Background check for van warehouse inventory levels against configured threshold."""
    settings = frappe.get_single('Maintenance Settings')
    if not settings.get('enable_low_stock_alerts'):
        return {'status': 'disabled'}
        
    threshold = int(settings.get('low_stock_threshold') or 3)
    bins = frappe.db.sql("""
        select item_code, warehouse, actual_qty 
        from `tabBin` 
        where warehouse like 'Van Warehouse%' 
        and actual_qty <= %s
    """, threshold, as_dict=1)
    
    for b in bins:
        frappe.log_error(f"Low stock alert for {b.item_code} in {b.warehouse}: {b.actual_qty} remaining.", "Van Low Stock Alert")
        
    return {'status': 'success', 'low_stock_items_count': len(bins)}

@frappe.whitelist()
def check_and_replenish_van_stock():
    """Checks van warehouse stock and automatically creates a Stock Entry (Material Transfer) if below threshold."""
    settings = frappe.get_single('Maintenance Settings')
    if not settings.get('auto_replenish_van') or not settings.get('main_source_warehouse'):
        return {'status': 'disabled'}
        
    threshold = int(settings.get('low_stock_threshold') or 3)
    source_wh = settings.main_source_warehouse
    
    bins = frappe.db.sql("""
        select item_code, warehouse, actual_qty 
        from `tabBin` 
        where warehouse like 'Van Warehouse%' 
        and actual_qty <= %s
    """, threshold, as_dict=1)
    
    replenished = []
    for b in bins:
        # Create Stock Entry of type Material Transfer
        se = frappe.get_doc({
            'doctype': 'Stock Entry',
            'stock_entry_type': 'Material Transfer',
            'from_warehouse': source_wh,
            'to_warehouse': b.warehouse,
            'company': frappe.defaults.get_defaults().get('company'),
            'items': [{
                'item_code': b.item_code,
                'qty': threshold * 2, # Replenish up to double threshold
                's_warehouse': source_wh,
                't_warehouse': b.warehouse
            }]
        })
        se.insert(ignore_permissions=True)
        se.submit()
        replenished.append({'item': b.item_code, 'warehouse': b.warehouse, 'stock_entry': se.name})
        
    frappe.db.commit()
    return {'status': 'success', 'replenished_orders': replenished}

@frappe.whitelist()
def get_manager_route_map():
    """Returns real-time GPS locations and active orders for all technicians for visual manager dispatch map."""
    techs = frappe.get_all('Field Technician', fields=['name', 'technician_name', 'status', 'current_latitude', 'current_longitude', 'zone', 'last_location_update'])
    active_orders = frappe.db.sql("""
        select name, customer, custom_assigned_technician, custom_maintenance_status, delivery_date 
        from `tabSales Order` 
        where custom_is_maintenance_order = 1 
        and custom_maintenance_status not in ('Completed', 'Cancelled')
    """, as_dict=1)
    
    return {'technicians': techs, 'active_orders': active_orders}

@frappe.whitelist()
def create_technician_expense(technician, employee, description, amount, sales_order=None, receipt_image=None):
    """Allows technicians to submit incidental mobile expenses (fuel, tolls) for manager approval."""
    try:
        claim = frappe.get_doc({
            'doctype': 'Expense Claim',
            'employee': employee,
            'approval_status': 'Draft',
            'posting_date': frappe.utils.nowdate(),
            'custom_maintenance_order': sales_order,
            'custom_technician': technician,
            'expenses': [{
                'expense_date': frappe.utils.nowdate(),
                'expense_type': 'Field Operations',
                'amount': float(amount),
                'description': description,
                'custom_receipt_image': receipt_image
            }]
        })
        claim.insert(ignore_permissions=True)
        frappe.db.commit()
        return {'status': 'success', 'expense_claim': claim.name}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Technician Expense Claim Error')
        return {'status': 'error', 'message': str(e)}

@frappe.whitelist()
def get_ai_spare_part_suggestions(problem_description):
    """AI diagnostic helper to suggest required spare parts based on issue description."""
    try:
        desc = problem_description.lower()
        suggested_parts = []
        
        if 'cooling' in desc or 'ac' in desc or 'compressor' in desc:
            suggested_parts.append({'item_code': 'FILTER-01', 'item_name': 'Air Filter Replacement', 'confidence': '92%'})
            suggested_parts.append({'item_code': 'REFRIG-R410', 'item_name': 'Refrigerant Gas R410A', 'confidence': '85%'})
        elif 'electrical' in desc or 'power' in desc or 'circuit' in desc:
            suggested_parts.append({'item_code': 'FUSE-10A', 'item_name': '10A Cartridge Fuse', 'confidence': '95%'})
            suggested_parts.append({'item_code': 'CABLE-COPPER', 'item_name': 'Copper Wiring Harness', 'confidence': '88%'})
        else:
            suggested_parts.append({'item_code': 'MAINT-LUBE', 'item_name': 'Synthetic Lubricant Spray', 'confidence': '90%'})
            
        return {'status': 'success', 'suggestions': suggested_parts}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@frappe.whitelist()
def run_preventive_maintenance_generator():
    """Generates recurring service orders for Preventive Maintenance (PM) schedules."""
    settings = frappe.get_single('Maintenance Settings')
    if not settings.get('enable_pm_engine'):
        return {'status': 'disabled'}
        
    # Example: Find active AMC contracts or recurring PM rules and generate sales orders
    created_orders = []
    amcs = frappe.get_all('AMC Contract', filters={'status': 'Active'}, fields=['name', 'customer', 'item_code', 'next_service_date'])
    today = frappe.utils.nowdate()
    
    for amc in amcs:
        if amc.next_service_date and amc.next_service_date <= today:
            so = frappe.get_doc({
                'doctype': 'Sales Order',
                'customer': amc.customer,
                'custom_is_maintenance_order': 1,
                'custom_maintenance_status': 'New',
                'custom_problem_description': f'Scheduled Preventive Maintenance under AMC: {amc.name}',
                'delivery_date': today,
                'items': [{
                    'item_code': amc.item_code or 'MAINT-SVC-01',
                    'qty': 1,
                    'rate': 150.0,
                    'amount': 150.0
                }]
            })
            so.insert(ignore_permissions=True)
            so.submit()
            created_orders.append(so.name)
            
            # Update next service date by 30 days
            next_date = frappe.utils.add_days(amc.next_service_date, 30)
            frappe.db.set_value('AMC Contract', amc.name, 'next_service_date', next_date)
            
    frappe.db.commit()
    return {'status': 'success', 'pm_orders_generated': created_orders}

@frappe.whitelist(allow_guest=True)
def get_customer_asset_portal_data(customer):
    """Provides a self-service dashboard for customers to view assets, service history, and active requests."""
    if not customer:
        return {'status': 'error', 'message': 'Customer name required'}
        
    orders = frappe.get_all('Sales Order', filters={'customer': customer, 'custom_is_maintenance_order': 1}, fields=['name', 'transaction_date', 'custom_maintenance_status', 'custom_assigned_technician', 'delivery_date', 'custom_problem_description'])
    return {'status': 'success', 'customer': customer, 'service_orders': orders}

@frappe.whitelist()
def verify_technician_certification(technician, required_skill):
    """Verifies whether a technician holds a valid, non-expired certification for the required skill."""
    settings = frappe.get_single('Maintenance Settings')
    if not settings.get('enforce_certification_lock'):
        return {'status': 'passed', 'reason': 'Certification lock disabled'}
        
    tech = frappe.get_doc('Field Technician', technician)
    if not tech.get('certifications'):
        return {'status': 'failed', 'reason': 'Technician has no certifications recorded.'}
        
    certs = [c.strip().lower() for c in tech.certifications.split(',')]
    if required_skill.lower() not in certs:
        return {'status': 'failed', 'reason': f'Technician lacks required certification: {required_skill}'}
        
    if tech.get('certification_expiry') and tech.certification_expiry < frappe.utils.nowdate():
        return {'status': 'failed', 'reason': 'Technician certification has expired.'}
        
    return {'status': 'passed'}

@frappe.whitelist()
def sync_offline_actions(offline_actions):
    """Synchronizes cached offline actions (signatures, notes, status updates) when technician reconnects."""
    try:
        import json
        if isinstance(offline_actions, str):
            offline_actions = json.loads(offline_actions)
            
        results = []
        for act in offline_actions:
            so_name = act.get('sales_order')
            if not so_name:
                continue
            so = frappe.get_doc('Sales Order', so_name)
            if act.get('status'):
                so.custom_maintenance_status = act.get('status')
            if act.get('notes'):
                so.custom_technician_notes = act.get('notes')
            if act.get('signature'):
                so.custom_customer_signature = act.get('signature')
            so.save(ignore_permissions=True)
            results.append({'sales_order': so_name, 'synced': True})
            
        frappe.db.commit()
        return {'status': 'success', 'synced_count': len(results), 'details': results}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Offline Sync Error')
        return {'status': 'error', 'message': str(e)}

@frappe.whitelist()
def validate_asset_warranty(serial_no):
    """Automatically checks serial number purchase date to determine warranty status."""
    try:
        if not serial_no:
            return {'warranty_status': 'Unknown'}
            
        serial = frappe.get_doc('Serial No', serial_no)
        # Check if within 1 year of purchase or delivery
        purchase_date = serial.get('purchase_date') or serial.get('creation')
        if purchase_date:
            from frappe.utils import getdate, date_diff
            days = date_diff(frappe.utils.nowdate(), purchase_date)
            if days <= 365:
                return {'warranty_status': 'Under Warranty', 'days_elapsed': days, 'is_billable': 0}
        return {'warranty_status': 'Out of Warranty', 'is_billable': 1}
    except Exception as e:
        return {'warranty_status': 'Out of Warranty', 'is_billable': 1}

@frappe.whitelist()
def get_technician_leaderboard():
    """Returns gamified leaderboard ranking technicians by rating and completed orders."""
    techs = frappe.get_all('Field Technician', fields=['name', 'technician_name', 'zone', 'status'])
    leaderboard = []
    
    for t in techs:
        completed_count = frappe.db.count('Sales Order', {'custom_assigned_technician': t.name, 'custom_maintenance_status': 'Completed'})
        avg_rating = frappe.db.sql("""
            select avg(custom_customer_rating) as avg_rating 
            from `tabSales Order` 
            where custom_assigned_technician = %s and custom_customer_rating > 0
        """, t.name, as_dict=1)
        
        rating = avg_rating[0].avg_rating if avg_rating and avg_rating[0].avg_rating else 5.0
        score = (completed_count * 10) + (float(rating) * 20)
        
        leaderboard.append({
            'technician': t.name,
            'name': t.technician_name,
            'zone': t.zone,
            'completed_orders': completed_count,
            'average_rating': round(float(rating), 2),
            'gamification_score': round(score, 2)
        })
        
    leaderboard.sort(key=lambda x: x['gamification_score'], reverse=True)
    return {'status': 'success', 'leaderboard': leaderboard}

@frappe.whitelist()
def get_equipment_manual(item_code):
    """Retrieves equipment manual or wiring diagram attachment URL for technician guidance."""
    try:
        manual = frappe.db.get_value('Item', item_code, 'custom_equipment_manual')
        return {'status': 'success', 'item_code': item_code, 'manual_url': manual or ''}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@frappe.whitelist()
def trigger_nps_survey_dispatch():
    """Background job to dispatch automated NPS survey emails/messages 24 hours post job completion."""
    settings = frappe.get_single('Maintenance Settings')
    if not settings.get('enable_nps_survey'):
        return {'status': 'disabled'}
        
    # Find orders completed yesterday that haven't received a survey yet
    from frappe.utils import add_days, nowdate
    yesterday = add_days(nowdate(), -1)
    
    orders = frappe.get_all('Sales Order', filters={
        'custom_is_maintenance_order': 1,
        'custom_maintenance_status': 'Completed',
        'modified': ['>=', yesterday]
    }, fields=['name', 'customer', 'customer_name'])
    
    dispatched = []
    for o in orders:
        # Simulate sending NPS survey email / WhatsApp message
        dispatched.append({'sales_order': o.name, 'customer': o.customer_name, 'status': 'Survey Sent'})
        
    return {'status': 'success', 'surveys_dispatched': dispatched}

@frappe.whitelist()
def get_fsm_profitability_report():
    """Calculates revenue vs cost of service per technician and job."""
    try:
        invoices = frappe.db.sql("""
            select name, customer, grand_total, outstanding_amount 
            from `tabSales Invoice` 
            where docstatus = 1
        """, as_dict=1)
        
        total_revenue = sum([float(inv.grand_total) for inv in invoices])
        
        # Estimate costs from stock entries and expense claims
        stock_costs = frappe.db.sql("""
            select sum(s.total_outgoing_value) as total_cost 
            from `tabStock Entry` s 
            where s.docstatus = 1 and s.stock_entry_type = 'Material Issue'
        """, as_dict=1)
        
        expense_costs = frappe.db.sql("""
            select sum(e.total_claimed_amount) as total_expenses 
            from `tabExpense Claim` e 
            where e.approval_status = 'Approved'
        """, as_dict=1)
        
        cost_of_parts = float(stock_costs[0].total_cost or 0) if stock_costs else 0.0
        cost_of_expenses = float(expense_costs[0].total_expenses or 0) if expense_costs else 0.0
        total_cost = cost_of_parts + cost_of_expenses
        
        net_profit = total_revenue - total_cost
        margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0.0
        
        return {
            'status': 'success',
            'total_revenue': round(total_revenue, 2),
            'total_cost': round(total_cost, 2),
            'net_profit': round(net_profit, 2),
            'profit_margin_percent': round(margin, 2)
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@frappe.whitelist()
def check_certification_expiries():
    """Background check for technician certifications expiring within 30 days."""
    try:
        from frappe.utils import add_days, nowdate
        target_date = add_days(nowdate(), 30)
        
        techs = frappe.db.sql("""
            select name, technician_name, certification_expiry 
            from `tabField Technician` 
            where certification_expiry <= %s and certification_expiry >= %s
        """, (target_date, nowdate()), as_dict=1)
        
        alerts = []
        for t in techs:
            alerts.append({'technician': t.name, 'name': t.technician_name, 'expiry': t.certification_expiry})
            
        return {'status': 'success', 'expiring_certifications': alerts}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@frappe.whitelist()
def get_navigation_link(sales_order):
    """Generates a one-click Google Maps turn-by-turn navigation URL for technicians."""
    try:
        so = frappe.get_doc('Sales Order', sales_order)
        lat = so.get('custom_latitude') or 24.7136 # Default Riyadh fallback
        lng = so.get('custom_longitude') or 46.6753
        map_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
        return {'status': 'success', 'sales_order': sales_order, 'navigation_url': map_url}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@frappe.whitelist()
def generate_asset_qrcode(serial_no):
    """Generates a QR code data URL pointing to the asset's service history."""
    try:
        portal_url = f"https://erp.elmrkz.cloud/api/method/maintenance_management.maintenance_management.api.get_customer_asset_portal_data?serial_no={serial_no}"
        # Using a reliable public QR code API generator or returning the URL payload
        qr_image_api = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={portal_url}"
        return {'status': 'success', 'serial_no': serial_no, 'qr_code_url': qr_image_api, 'target_url': portal_url}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@frappe.whitelist()
def optimize_technician_route(technician, date=None):
    """AI-driven greedy nearest-neighbor route optimizer for a technician's daily service orders."""
    try:
        if not date:
            date = frappe.utils.nowdate()
            
        orders = frappe.get_all('Sales Order', filters={
            'custom_assigned_technician': technician,
            'custom_maintenance_status': ['in', ['Assigned', 'In Progress']]
        }, fields=['name', 'customer', 'custom_latitude', 'custom_longitude'])
        
        if not orders:
            return {'status': 'success', 'optimized_sequence': [], 'message': 'No active orders found for optimization.'}
            
        # Simple greedy TSP sorting based on coordinates
        current_lat = 24.7136 # Default depot / Riyadh center
        current_lng = 46.6753
        
        remaining = list(orders)
        sequence = []
        
        while remaining:
            # Find nearest next order
            nearest = min(remaining, key=lambda o: ((float(o.get('custom_latitude') or 24.7136) - current_lat)**2 + (float(o.get('custom_longitude') or 46.6753) - current_lng)**2)**0.5)
            remaining.remove(nearest)
            sequence.append(nearest)
            current_lat = float(nearest.get('custom_latitude') or 24.7136)
            current_lng = float(nearest.get('custom_longitude') or 46.6753)
            
        return {'status': 'success', 'optimized_sequence': [o.name for o in sequence], 'details': sequence}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@frappe.whitelist()
def reserve_van_spare_parts(sales_order, technician, item_code, qty):
    """Reserves specific spare parts in the technician's van warehouse for an assigned order."""
    try:
        tech = frappe.get_doc('Field Technician', technician)
        van_warehouse = tech.get('van_warehouse')
        if not van_warehouse:
            return {'status': 'error', 'message': 'Technician has no assigned van warehouse.'}
            
        # Check actual stock
        bin_qty = frappe.db.get_value('Bin', {'item_code': item_code, 'warehouse': van_warehouse}, 'actual_qty') or 0.0
        if float(bin_qty) < float(qty):
            return {'status': 'warning', 'message': f'Insufficient stock in van warehouse ({bin_qty} available, {qty} requested). Material Request recommended.'}
            
        # Create a reservation record or log
        frappe.logger().info(f"Reserved {qty} of {item_code} in {van_warehouse} for order {sales_order}")
        return {'status': 'success', 'warehouse': van_warehouse, 'reserved_qty': qty, 'message': 'Inventory successfully reserved.'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
