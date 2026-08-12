frappe.ui.form.on('Field Service Request', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Run AI Diagnostics'), function() {
                frappe.call({
                    method: 'run_ai_diagnostics',
                    doc: frm.doc,
                    callback: function(r) {
                        if (!r.exc) {
                            frm.reload_doc();
                            frappe.msgprint(__('AI Diagnostics completed! Suggested parts and estimate populated.'));
                        }
                    }
                });
            }).addClass('btn-primary');
        }
    }
});
