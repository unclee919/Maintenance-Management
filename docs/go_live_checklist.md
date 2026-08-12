# Field Service Management: Go-Live Operational Checklist
**Author:** Manus AI  
**Target System:** Frappe v16 / ERPNext (`erp.elmrkz.cloud`)  
**Repository:** [unclee919/Maintenance-Management](https://github.com/unclee919/Maintenance-Management)

---

## 1. Introduction
This Go-Live Operational Checklist is designed for system administrators, operations managers, and field supervisors deploying the custom **Field Maintenance Management** suite on Frappe v16. Completing these validation steps ensures a seamless transition from testing to live production operations.

---

## 2. Pre-Flight Desk Configuration (Zero-Hardcode)
Before opening the system to live technicians and customers, verify the global settings under **Maintenance Settings** in Frappe Desk:
* **Weighted Assignment Criteria:** Ensure the 7 criteria weights total exactly 100% (Proximity, Skill Match, Availability, Workload Balance, Performance, Zone, Route).
* **Automation Toggles:** Confirm that `auto_create_invoice` and `auto_create_stock_entry` are enabled to streamline financial processing upon job completion.
* **Shift Enforcement:** Verify that technician shift start and end times are populated in their **Field Technician** profiles to enable shift-aware queueing.
* **Notification Channels:** Enable SMS, WhatsApp, or Push notification gateways as required by your communication infrastructure.

---

## 3. Master Data Verification
Ensure all essential master data records are created and linked correctly in the system:
* **Field Technicians:** Verify that technician profiles are active, assigned to valid service zones, linked to their respective **Van Warehouses**, and have their skill matrices rated.
* **Maintenance Items:** Confirm that spare parts and service items have correct pricing rules, default service fees, and attached equipment manuals or wiring diagrams.
* **AMC Contracts:** Verify that active AMC customer contracts have correct recurring schedule intervals for the Preventive Maintenance (PM) engine.

---

## 4. End-to-End Simulation Test
Execute a dry-run test transaction to validate the complete lifecycle:
1. Create a test **Sales Order** with a maintenance item and flag it as active.
2. Verify that the weighted assignment engine automatically allocates the optimal technician based on Desk criteria.
3. Simulate technician mobile portal login, trip start, **one-click Google Maps navigation**, and completion with digital signature capture and QC checklist verification.
4. Verify that the **Sales Invoice** and **Stock Entry** (spare parts consumption) are automatically generated in ERPNext.

---
*End of Go-Live Checklist.*
