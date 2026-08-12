import frappe
from frappe.model.document import Document

class ServiceAppointment(Document):
    def validate(self):
        if not self.appointment_id:
            self.appointment_id = frappe.generate_hash('Service Appointment', 10)
