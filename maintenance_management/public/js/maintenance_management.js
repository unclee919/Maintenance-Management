// Maintenance Management Global JS
$(document).ready(function() {
    // Request notification permission on load
    if (Notification.permission === "default") {
        Notification.requestPermission();
    }

    // Listen for real-time maintenance notifications
    frappe.realtime.on("maintenance_notification", function(data) {
        // 1. Show Browser Native Notification
        if (Notification.permission === "granted") {
            var n = new Notification(data.title, {
                body: data.message,
                icon: "/assets/maintenance_management/images/icon.png",
                tag: data.docname // Prevent duplicates
            });
            n.onclick = function() {
                window.focus();
                frappe.set_route("Form", "Service Appointment", data.docname);
            };
        }

        // 2. Show Frappe Alert
        frappe.show_alert({
            message: __("<b>{0}</b><br>{1}", [data.title, data.message]),
            indicator: 'blue'
        }, 7);

        // 3. Play notification sound if possible
        try {
            var audio = new Audio('/assets/maintenance_management/sounds/notification.mp3');
            audio.play();
        } catch (e) {}
    });
});
