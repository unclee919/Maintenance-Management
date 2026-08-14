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
    },
    check_connectivity: function(frm) {
        frappe.show_alert({message: __("Checking connectivity..."), indicator: 'orange'});
        fetch(window.location.origin + "/api/method/frappe.ping")
            .then(response => {
                if (response.ok) {
                    frappe.msgprint({
                        title: __("Connectivity OK"),
                        message: __("Your browser can successfully reach the server at {0}.", [window.location.origin]),
                        indicator: 'green'
                    });
                } else {
                    frappe.msgprint({
                        title: __("Server Error"),
                        message: __("Server reached but returned an error: {0}", [response.status]),
                        indicator: 'red'
                    });
                }
            })
            .catch(error => {
                frappe.msgprint({
                    title: __("Connection Failed"),
                    message: __("DNS or Network Error: Could not reach the server. Please check your internet or DNS settings."),
                    indicator: 'red'
                });
            });
    }
});
