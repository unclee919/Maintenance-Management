# Field Maintenance Management System: User Training Guide

Welcome to the **Field Maintenance Management** system, built on Frappe v16 and integrated with ERPNext. This document serves as the official training guide for dispatchers, managers, and field technicians.

---

## 1. Overview for Dispatchers & Managers

The **Management Dashboard** provides real-time oversight of all field service operations, active work orders, and technician workloads.

### Key Responsibilities:
* **Monitoring Service Orders**: Access your dashboard via the sidebar module **Maintenance Management** $\rightarrow$ **Management Dashboard**.
* **SLA Tracking**: Review the `SLA Status` field (`On Time`, `Warning`, `Breached`). Orders approaching delivery deadlines are automatically highlighted.
* **Executive Charts**: Analyze **Field Revenue by Equipment Type** and technician utilization through built-in dashboard charts.
* **Automated SLA Escalation**: The system automatically scans for orders stuck in *In Progress* for over 48 hours and logs administrative alerts.

---

## 2. Guide for Field Technicians

Field engineers use the mobile-optimized **Technician Dashboard** to manage their assigned jobs on the go.

### Daily Workflow Steps:
1. **Accessing Assigned Orders**: Log into Frappe Desk on your mobile browser or tablet and open the **Technician Dashboard** workspace. Tap **My Assigned Orders** to see your filtered task list.
2. **Reviewing Equipment Details**: Open your assigned `Sales Order` to inspect the `Equipment Type`, `Equipment Serial No`, and `Issue Description`.
3. **Accepting and Starting Work**:
   * Change status from `Assigned` to `Accepted` when you acknowledge the job.
   * Change status to `In Progress` when you arrive on-site.
4. **Running AI Diagnostics**:
   * Tap or execute the **Run AI Diagnostics** action button on the order view.
   * The system will automatically analyze the issue description and suggest required spare parts (e.g., *Refrigerant R410A* or *Fan Motor Bearings*) along with estimated repair pricing.
5. **Capturing Proof of Service**:
   * **Customer Signature**: Have the client sign directly in the `Customer Signature` signature field.
   * **Service Photo**: Upload a photo of the completed repair in the `Service Completion Photo` attachment field.
6. **Completing the Task & Inventory Deduction**:
   * Set status to `Completed` and record the customer's `Feedback Score`.
   * Saving the completed order automatically triggers an ERPNext **Material Issue Stock Entry**, deducting consumed parts directly from your assigned **Van Warehouse** (e.g., `Van Stock - Marcus`).

---

## 3. System Administration & Settings

Administrators can configure global system toggles under **Field Maintenance Settings**:
* **Auto-Assign Technician**: Toggle automated matching based on technician availability and equipment specialty skills (`specialty_equipment`).
* **Webhook URL**: Connect external automation platforms (such as **n8n**) to broadcast real-time status updates and customer feedback surveys.

---
*Default Author: **Manus AI** | System: ERPNext / Frappe v16*
