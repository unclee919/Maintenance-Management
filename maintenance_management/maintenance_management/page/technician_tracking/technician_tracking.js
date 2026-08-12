
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
            <div class="row">
                <div class="col-md-12">
                    <div class="card mb-4">
                        <div class="card-header bg-dark text-white"><strong>📈 Predictive Spare Parts Consumption Forecast (Next 7 Days)</strong></div>
                        <div class="card-body" id="forecast-container">
                            <p>Loading forecast analytics...</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="card">
                <div class="card-header bg-secondary text-white"><strong>Live Map Simulator & Geofence Alerts</strong></div>
                <div class="card-body text-center" style="min-height: 250px; background: #f8f9fa;">
                    <div id="map-simulator-view" class="p-4">
                        <h4>📍 GPS Live Tracking & Geofence View (Cairo / Giza Region)</h4>
                        <p class="text-muted">Automatic geofencing triggers alerts when technicians enter within 500m of customer locations.</p>
                        <div class="btn-group mt-3" role="group">
                            <button class="btn btn-outline-primary" onclick="frappe.show_alert('Refreshing GPS pings...')">🔄 Refresh GPS Feed</button>
                            <button class="btn btn-outline-success" onclick="test_geofence_simulation()">📍 Simulate Geofence Arrival</button>
                            <button class="btn btn-outline-danger" onclick="frappe.show_alert('Emergency dispatch broadcast sent!')">🚨 Emergency Broadcast</button>
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


function load_forecast() {
    frappe.call({
        method: "maintenance_management.maintenance_management.api.get_spare_parts_forecast",
        callback: function(r) {
            if (r && r.message && r.message.items) {
                let items = r.message.items;
                let html = `<table class="table table-bordered table-striped">
                    <thead><tr><th>Item Code</th><th>Item Name</th><th>Current Stock</th><th>Predicted Demand (7 Days)</th><th>Status</th></tr></thead>
                    <tbody>`;
                items.forEach(i => {
                    let statusBadge = i.current_stock >= i.predicted_demand ? '<span class="badge badge-success">Sufficient</span>' : '<span class="badge badge-danger">Reorder Advised</span>';
                    html += `<tr>
                        <td><strong>${i.item_code}</strong></td>
                        <td>${i.item_name}</td>
                        <td>${i.current_stock}</td>
                        <td>${i.predicted_demand}</td>
                        <td>${statusBadge}</td>
                    </tr>`;
                });
                html += '</tbody></table>';
                $('#forecast-container').html(html);
            }
        }
    });
}

function test_geofence_simulation() {
    frappe.call({
        method: "maintenance_management.maintenance_management.api.check_geofence_arrival",
        args: {
            sales_order: "SO-00001",
            tech_lat: 30.0444,
            tech_lon: 31.2357
        },
        callback: function(r) {
            if (r && r.message) {
                frappe.msgprint({
                    title: __('Geofence Arrival Simulation'),
                    indicator: 'green',
                    message: __('Geofence Status: {0}<br>Distance: {1} meters<br>{2}', [r.message.arrived ? 'ARRIVED' : 'EN ROUTE', r.message.distance_meters, r.message.alert])
                });
            }
        }
    });
}

// Call load_forecast inside load_tracking_data or on page load
setTimeout(load_forecast, 1000);
