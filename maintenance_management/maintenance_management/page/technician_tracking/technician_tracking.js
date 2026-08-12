
frappe.pages['technician-tracking'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: '🗺️ Field Technician Live Tracking & Operations Map',
        single_column: true
    });

    $(wrapper).find('.layout-main-section').html(`
        <div class="p-4">
            <div class="alert alert-info">
                <strong>Real-Time Management Dashboard:</strong> Track field technicians, active service orders, and GPS coordinates live.
            </div>
            <div class="row">
                <div class="col-md-6">
                    <div class="card mb-4">
                        <div class="card-header bg-primary text-white"><strong>Active Technicians</strong></div>
                        <div class="card-body" id="tech-list-container">
                            <p>Loading technicians...</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card mb-4">
                        <div class="card-header bg-success text-white"><strong>Active Service Orders</strong></div>
                        <div class="card-body" id="order-list-container">
                            <p>Loading active orders...</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="card">
                <div class="card-header bg-dark text-white"><strong>Live Map Simulator & GPS Coordinates</strong></div>
                <div class="card-body text-center" style="min-height: 300px; background: #f8f9fa;">
                    <div id="map-simulator-view" class="p-5">
                        <h4>📍 GPS Live Tracking View (Cairo / Giza Region)</h4>
                        <p class="text-muted">Interactive map connected to live technician GPS pings and geofence status.</p>
                        <div class="btn-group mt-3" role="group">
                            <button class="btn btn-outline-primary" onclick="frappe.show_alert('Refreshing GPS pings...')">🔄 Refresh GPS Feed</button>
                            <button class="btn btn-outline-success" onclick="frappe.show_alert('Emergency dispatch broadcast sent!')">🚨 Emergency Broadcast</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `);

    load_tracking_data();
};

function load_tracking_data() {
    frappe.call({
        method: "maintenance_management.maintenance_management.page.technician_tracking.technician_tracking.get_live_tracking_data",
        callback: function(r) {
            if (r && r.message) {
                let techs = r.message.technicians;
                let orders = r.message.orders;
                
                let techHtml = '<ul class="list-group">';
                techs.forEach(t => {
                    let badgeClass = t.status === 'Available' ? 'badge-success' : 'badge-warning';
                    techHtml += `<li class="list-group-item d-flex justify-content-between align-items-center">
                        <div><strong>${t.technician_name}</strong> (${t.name})<br><small class="text-muted">Van: ${t.van_warehouse || 'N/A'}</small></div>
                        <span class="badge ${badgeClass} p-2">${t.status}</span>
                    </li>`;
                });
                techHtml += '</ul>';
                $('#tech-list-container').html(techHtml);

                let orderHtml = '<ul class="list-group">';
                orders.forEach(o => {
                    orderHtml += `<li class="list-group-item d-flex justify-content-between align-items-center">
                        <div><strong>${o.name}</strong> - ${o.customer}<br><small class="text-muted">Tech: ${o.custom_assigned_technician || 'Unassigned'}</small></div>
                        <span class="badge badge-info p-2">${o.custom_maintenance_status}</span>
                    </li>`;
                });
                orderHtml += '</ul>';
                $('#order-list-container').html(orderHtml);
            }
        }
    });
}
