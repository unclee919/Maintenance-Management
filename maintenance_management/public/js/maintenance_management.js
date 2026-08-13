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

    // Listen for real-time maintenance notifications
    if (typeof frappe !== "undefined" && frappe.realtime) {
        console.log("Maintenance Management: Real-time listener initialized.");
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
            
            // 3. Show Frappe Toast Alert
            if (typeof frappe.show_alert === "function") {
                frappe.show_alert({
                    message: __("<b>{0}</b><br>{1}", [data.title, data.message]),
                    indicator: 'blue'
                }, 10);
            }

            // 4. Update the notification bell count
            if (frappe.ui.notifications) {
                frappe.ui.notifications.update_notifications();
            }
        });
    }
});
