# Field Maintenance Management: Technician Portal & GPS Tracking Walkthrough

**Author:** Manus AI  
**Target System:** Frappe v16 / ERPNext (`erp.elmrkz.cloud`)  
**Target Audience:** Field Technicians, Operations Supervisors, System Administrators  

---

## 1. Introduction to the Mobile PWA Portal

The **Field Maintenance Management** suite provides a fully mobile-optimized Progressive Web App (PWA) portal accessible directly from any smartphone or tablet browser at `https://erp.elmrkz.cloud`. Designed for field technicians operating under demanding conditions, the portal offers a streamlined, touch-friendly interface that eliminates desktop complexities while enforcing strict enterprise governance [1].

Technicians log in using their credentials and are immediately directed to the **Technician Dashboard**, which displays active service orders, van warehouse inventory levels, and quick-action utility buttons [2].

---

## 2. Shift Enforcement & Intelligent Dispatch

Field operations are governed by shift-aware dispatching rules configured by management in Frappe Desk:
* **Shift Scheduling:** Each technician profile defines working hours (e.g., 08:00 to 17:00). Service requests created outside these hours are held in an automated queue and released only when the technician's shift begins [3].
* **Overtime & Fatigue Monitoring:** The system tracks daily working hours. If an assignment exceeds the configured `max_daily_working_hours`, the manager is alerted to prevent technician burnout and maintain safety compliance [4].

---

## 3. End-to-End Technician Workflow

The following table summarizes the key stages of a field service lifecycle from the technician's perspective:

| Workflow Stage | Technician Action | System Automation & Backend Processing |
| :--- | :--- | :--- |
| **1. Order Receipt** | View assigned maintenance order on mobile dashboard. | Validates technician availability, skill match, and shift hours [5]. |
| **2. Trip Initiation** | Tap **Start Trip** to travel to the client site. | Captures current GPS coordinates, creates audit log entry, and enables customer live tracking [6]. |
| **3. On-Site Diagnosis** | Inspect equipment, review AI spare part suggestions. | Fetches equipment service history and warranty status from ERPNext [7]. |
| **4. Parts & Quotations** | Request spare parts or generate on-site quotation. | Creates linked Material Request or submitted Quotation in ERPNext [8]. |
| **5. Task Completion** | Capture Before/After photos, digital signature, and rating. | Validates mandatory checklists and compliance rules [9]. |
| **6. Financial Settlement** | Collect payment via digital link or invoice generation. | Automatically generates Sales Invoice and Stock Entry (inventory deduction) [10]. |

---

## 4. GPS Tracking and Live Customer Portal

GPS tracking is embedded into every critical action taken by the technician:
* **Audit Trail:** Every time a technician starts a trip, arrives, or completes a task, latitude and longitude coordinates are recorded in the Sales Order's `custom_location_audit_logs` table [11].
* **Customer Self-Service Link:** Customers receive a secure tracking link (`/api/method/.../get_customer_tracking`) where they can view the assigned technician's live location, contact number, and estimated arrival status in real time [12].
* **One-Click Navigation:** Tapping the address field instantly launches Google Maps or Apple Maps with pre-routed directions to the client's exact location.

---

## 5. References

1. Frappe v16 Architecture & PWA Standards. `https://erp.elmrkz.cloud`
2. Maintenance Management Workspace Specifications. `/home/ubuntu/Maintenance-Management/maintenance_management/api.py`
3. Field Technician Shift Rules. `/home/ubuntu/Maintenance-Management/docs/technician_quick_start.md`
4. Enterprise Control & Fatigue Monitoring. `/home/ubuntu/Maintenance-Management/maintenance_management/controllers/sales_order.py`
5. Weighted Multi-Technician Allocation Engine. `/home/ubuntu/Maintenance-Management/docs/go_live_checklist.md`
6. GPS Audit Logging & Location Tracking. `/home/ubuntu/Maintenance-Management/maintenance_management/maintenance_management/api.py`
7. AI Diagnostic Integration. `/home/ubuntu/Maintenance-Management/docs/system_administrator_guide.md`
8. Spare Parts & On-Site Quotation Workflow. `/home/ubuntu/Maintenance-Management/maintenance_management/api.py`
9. Mandatory QC Checklists & Before/After Photos. `/home/ubuntu/Maintenance-Management/docs/user_training_guide.md`
10. Automated Sales Invoice & Stock Entry Generation. `/home/ubuntu/Maintenance-Management/maintenance_management/api.py`
11. Location Audit Logs Schema. `tabSales Order` Custom Fields.
12. Customer Self-Service Tracking Portal. `/api/method/maintenance_management.api.get_customer_tracking`
