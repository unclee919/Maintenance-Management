# Field Maintenance Management: Manager Training & Operations Guide

**Author**: Manus AI  
**Target Audience**: Operations Managers, Service Supervisors, and System Administrators  
**System URL**: [https://erp.elmrkz.cloud](https://erp.elmrkz.cloud)  

---

## Slide 1: Welcome & Executive Overview

Welcome to the **Field Maintenance Management** training program. This session covers the newly deployed operational features in ERPNext, designed to streamline end-to-end service delivery from initial customer request to automated inventory deduction and billing.

> "Our goal is zero manual data entry, real-time dispatch visibility, and automated accounting reconciliation."

---

## Slide 2: Zero-Hardcode Configuration via Frappe Desk

All business rules, thresholds, and assignment criteria are managed dynamically through the **Field Maintenance Settings** doctype in Frappe Desk. No code changes are required to adjust system behavior.

| Configuration Parameter | Description | Default Setting |
| :--- | :--- | :--- |
| **Default Van Warehouse** | Source warehouse for technician parts consumption | `Stores - E` |
| **Assignment Algorithm** | Matching rule for incoming service orders | `Skill & Zone Match` |
| **SLA Escalation Hours** | Warning threshold before notifying supervisors | `24 Hours` |
| **GPS Tracking Interval** | Ping frequency during active technician trips | `5 Minutes` |

---

## Slide 3: Automated Technician Assignment Workflow

When a Sales Order is created (either manually or via external integrations like n8n), the system automatically evaluates order items and customer territory against technician profiles.

```
[Sales Order Created] ➔ [Check Assignment Criteria] ➔ [Match Zone & Skill] ➔ [Assign Technician(s)] ➔ [Push In-App & Browser Alert]
```

- **Multi-Item & Multi-Technician Support**: Complex orders with multiple equipment types or service requirements can be split across specialized technicians.
- **Immediate Notifications**: Assigned technicians and managers receive instant in-app alerts with actionable quick-buttons (*Accept*, *Start Trip*, *Complete*).

---

## Slide 4: Real-Time Location Tracking & GPS Navigation

Once a technician accepts a task and clicks **"Start Trip"**, the mobile portal initiates live GPS telemetry.

- **Periodic Location Pings**: Coordinates are sent back to the ERP backend at configurable intervals.
- **Error Resilience**: If a technician denies browser location access or loses GPS signal, the system logs a warning, alerts dispatch, and allows manual status overrides.
- **One-Click Navigation**: Technicians can tap **"Open in Maps"** to launch turn-by-turn routing directly to the client's site.

---

## Slide 5: The Public Client Tracking Portal

Customers do not need an ERP login to track their service progress.

1. **Automated SMS/Email Link**: Upon dispatch, the client receives a secure tracking link (e.g., `https://erp.elmrkz.cloud/track/SO-2026-00125`).
2. **Live Map & ETA**: The client can view the technician's real-time position and estimated time of arrival.
3. **Rescheduling Option**: If plans change, clients can select a new preferred date and time directly from the tracking portal, which automatically updates the Sales Order and notifies management.

---

## Slide 6: Enhanced Invoicing & ERPNext Pricing Rules

Task completion triggers automated ERPNext financial and inventory workflows.

- **Pricing Rules Engine**: Automatically applies volume discounts, special contract rates, and regional pricing matrices defined in ERPNext.
- **Stock Entry (Material Issue)**: Replacement parts are instantly deducted from the technician's assigned Van Warehouse.
- **Clean Sales Invoice**: Aggregates general service fees, labor hours, and parts into a single professional invoice linked to the original Sales Order.

---

## Slide 7: Q&A and System Access

- **Live System**: [https://erp.elmrkz.cloud](https://erp.elmrkz.cloud)
- **Admin Credentials**: `Administrator` / `Pass12345`
- **Support Repository**: [GitHub Maintenance Management](https://github.com/unclee919/Maintenance-Management)

---
*References:* [1] ERPNext v16 Documentation (https://frappeframework.com) [2] Field Maintenance Management Technical Specifications.
