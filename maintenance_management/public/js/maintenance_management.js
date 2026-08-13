// Maintenance Management Global JS & Push Notification Handler
$(document).ready(function() {
    console.log("Maintenance Management: Global script loaded.");

    // Request browser notification permission
    if (typeof Notification !== "undefined" && Notification.permission === "default") {
        Notification.requestPermission();
    }

    // Function to play customizable audio alerts
    function playAlertSound(soundType, customFileUrl) {
        console.log("Maintenance Management: Playing sound", soundType, customFileUrl);
        
        // Handle custom file upload
        if (soundType === "Custom" && customFileUrl) {
            try {
                var audio = new Audio(customFileUrl);
                audio.play().catch(e => console.log("Custom audio play error:", e));
                return;
            } catch (e) {
                console.log("Audio file error:", e);
            }
        }

        // Fallback to Web Audio API synthesis
        try {
            var audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            var osc = audioCtx.createOscillator();
            var gain = audioCtx.createGain();
            osc.connect(gain);
            gain.connect(audioCtx.destination);

            var now = audioCtx.currentTime;

            if (soundType === "Chime") {
                osc.type = "sine";
                osc.frequency.setValueAtTime(587.33, now); // D5
                osc.frequency.setValueAtTime(880.00, now + 0.15); // A5
                gain.gain.setValueAtTime(0.2, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
                osc.start(now);
                osc.stop(now + 0.6);
            } else if (soundType === "Beep") {
                osc.type = "square";
                osc.frequency.setValueAtTime(440, now);
                gain.gain.setValueAtTime(0.15, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);
                osc.start(now);
                osc.stop(now + 0.3);
            } else if (soundType === "Alert") {
                osc.type = "sawtooth";
                osc.frequency.setValueAtTime(300, now);
                osc.frequency.setValueAtTime(600, now + 0.1);
                osc.frequency.setValueAtTime(300, now + 0.2);
                gain.gain.setValueAtTime(0.2, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
                osc.start(now);
                osc.stop(now + 0.5);
            } else {
                // Default
                osc.type = "sine";
                osc.frequency.setValueAtTime(500, now);
                gain.gain.setValueAtTime(0.1, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);
                osc.start(now);
                osc.stop(now + 0.3);
            }
        } catch (e) {
            console.log("Audio synthesis error:", e);
        }
    }

    function initMaintenanceRealtime() {
        if (typeof frappe !== "undefined" && frappe.realtime) {
            console.log("Maintenance Management: Real-time listener initialized.");
            frappe.realtime.off("maintenance_notification"); // Prevent duplicate listeners
            frappe.realtime.on("maintenance_notification", function(data) {
                console.log("Maintenance Notification Received:", data);
                
                // 1. Play Sound
                playAlertSound(data.sound, data.sound_file);

                // 2. Show Browser Native Push Notification
                if (typeof Notification !== "undefined" && Notification.permission === "granted") {
                    try {
                        var n = new Notification(data.title, {
                            body: data.message,
                            tag: data.docname,
                            icon: "/assets/maintenance_management/octicon-tools.png"
                        });
                        n.onclick = function() {
                            window.focus();
                            frappe.set_route("Form", "Service Appointment", data.docname);
                        };
                    } catch (e) {
                        console.log("Push notification error:", e);
                    }
                }
                
                // 3. Show Floating Bottom-Right Notification Banner (Facebook / Web App style)
                var bannerId = 'maint-notif-' + Date.now();
                var bannerHtml = `
                    <div id="${bannerId}" style="position: fixed; bottom: 20px; right: 20px; z-index: 99999; background: #ffffff; border-left: 4px solid #1a73e8; box-shadow: 0 10px 25px rgba(0,0,0,0.15); border-radius: 8px; padding: 16px; width: 340px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; animation: slideInUp 0.3s ease;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                            <div style="font-weight: 600; font-size: 14px; color: #1f2937;">${data.title}</div>
                            <button onclick="document.getElementById('${bannerId}').remove();" style="background: none; border: none; font-size: 16px; cursor: pointer; color: #9ca3af; line-height: 1;">&times;</button>
                        </div>
                        <div style="font-size: 13px; color: #4b5563; margin-bottom: 12px; line-height: 1.4; white-space: pre-line;">${data.message}</div>
                        <div style="display: flex; gap: 8px;">
                            <button onclick="frappe.call({method: 'maintenance_management.controllers.sales_order.accept_dispatch', args: {appointment_name: '${data.docname}'}, callback: function(r){ frappe.show_alert('Dispatch Accepted!'); document.getElementById('${bannerId}').remove(); }})" style="background: #10b981; color: #fff; border: none; padding: 6px 12px; border-radius: 4px; font-size: 12px; font-weight: 500; cursor: pointer;">Accept</button>
                            <button onclick="frappe.call({method: 'maintenance_management.controllers.sales_order.reject_dispatch', args: {appointment_name: '${data.docname}'}, callback: function(r){ frappe.show_alert('Dispatch Rejected'); document.getElementById('${bannerId}').remove(); }})" style="background: #ef4444; color: #fff; border: none; padding: 6px 12px; border-radius: 4px; font-size: 12px; font-weight: 500; cursor: pointer;">Reject</button>
                            <button onclick="frappe.set_route('Form', 'Service Appointment', '${data.docname}'); document.getElementById('${bannerId}').remove();" style="background: #3b82f6; color: #fff; border: none; padding: 6px 12px; border-radius: 4px; font-size: 12px; font-weight: 500; cursor: pointer;">Details</button>
                        </div>
                    </div>
                `;
                $('body').append(bannerHtml);

                // 4. Show Frappe Toast Alert
                if (typeof frappe.show_alert === "function") {
                    frappe.show_alert({
                        message: __("<b>{0}</b><br>{1}", [data.title, data.message]),
                        indicator: 'blue'
                    }, 10);
                }

                // 5. Update the notification bell count
                if (frappe.ui.notifications) {
                    frappe.ui.notifications.update_notifications();
                }
            });
        }
    }

    initMaintenanceRealtime();
    setTimeout(initMaintenanceRealtime, 2000);
});
