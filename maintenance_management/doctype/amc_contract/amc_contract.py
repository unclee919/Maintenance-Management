import frappe
from frappe.model.document import Document
from frappe.utils import getdate, add_days, today

class AMCContract(Document):
    def validate(self):
        if not self.contract_name:
            self.contract_name = frappe.generate_hash('AMC Contract', 10)
        if self.start_date and not self.next_service_date:
            self.next_service_date = self.start_date

def generate_amc_service_requests():
    """Scheduled task to generate recurring service requests from active AMC Contracts."""
    active_contracts = frappe.get_all('AMC Contract', filters={'status': 'Active', 'next_service_date': ['<=', today()]})
    
    for contract in active_contracts:
        doc = frappe.get_doc('AMC Contract', contract.name)
        
        # Create Service Request
        sr = frappe.get_doc({
            'doctype': 'Service Request',
            'customer': doc.customer,
            'priority': 'Medium',
            'issue_description': f'Scheduled AMC Service Request under contract {doc.contract_name}',
            'service_type': doc.service_type,
            'assigned_technician': doc.assigned_technician
        })
        sr.insert(ignore_permissions=True)
        sr.submit()
        
        # Update next service date based on frequency
        interval_days = 30
        if doc.billing_frequency == 'Quarterly':
            interval_days = 90
        elif doc.billing_frequency == 'Semi-Annually':
            interval_days = 180
        elif doc.billing_frequency == 'Annually':
            interval_days = 365
            
        doc.last_generated_date = today()
        doc.next_service_date = add_days(getdate(doc.next_service_date), interval_days)
        doc.save(ignore_permissions=True)
        
        frappe.logger().info(f'Generated recurring service request {sr.name} for AMC contract {doc.contract_name}')
