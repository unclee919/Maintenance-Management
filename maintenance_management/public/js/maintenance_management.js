// Maintenance Management Global JS & Push Notification Handler
$(document).ready(function() {
    // Request browser notification permission
    if (typeof Notification !== "undefined" && Notification.permission === "default") {
        Notification.requestPermission();
    }

    // Function to play customizable audio alerts using Web Audio API
    function playAlertSound(soundType) {
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
            console.log("Audio play error:", e);
        }
    }

    // Listen for real-time maintenance notifications
    if (typeof frappe !== "undefined" && frappe.realtime) {
        frappe.realtime.on("maintenance_notification", function(data) {
            // 1. Show Browser Native Push Notification
            if (typeof Notification !== "undefined" && Notification.permission === "granted") {
                try {
                    var n = new Notification(data.title, {
                        body: data.message,
                        tag: data.docname
                    });
                    n.onclick = function() {
                        window.focus();
                        frappe.set_route("Form", "Service Appointment", data.docname);
                    };
                } catch (e) {}
            }

            // 2. Show Frappe Toast Alert
            if (typeof frappe.show_alert === "function") {
                frappe.show_alert({
                    message: __("<b>{0}</b><br>{1}", [data.title, data.message]),
                    indicator: 'blue'
                }, 10);
            }

            // 3. Play Sound Effect
            playAlertSound(data.sound || "Chime");
        });
    }
});
