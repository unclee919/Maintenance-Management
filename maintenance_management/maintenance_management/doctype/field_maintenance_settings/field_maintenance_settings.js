frappe.ui.form.on('Field Maintenance Settings', {
    refresh: function(frm) {
        // Request notification permission if not granted
        if (Notification.permission === "default") {
            frm.add_custom_button(__('Enable Browser Notifications'), function() {
                Notification.requestPermission().then(permission => {
                    if (permission === "granted") {
                        frappe.msgprint(__("Browser notifications enabled!"));
                    }
                });
            });
        }
    },
    test_notification: function(frm) {
        frappe.call({
            method: "maintenance_management.maintenance_management.api.test_technician_notification",
            args: {
                user: frappe.session.user
            },
            callback: function(r) {
                if (!r.exc) {
                    frappe.show_alert({
                        message: __("Test notification triggered! Check your bell icon and browser pop-ups."),
                        indicator: 'green'
                    });
                }
            }
        });
    }
});
