frappe.ui.form.on('Service Appointment', {
    refresh: function(frm) {
        frm.add_custom_button(__('Open Map Location'), function() {
            if (frm.doc.location) {
                window.open(`https://maps.google.com/?q=${encodeURIComponent(frm.doc.location)}`, '_blank');
            } else {
                frappe.msgprint(__('No location specified for this appointment.'));
            }
        });
    }
});
