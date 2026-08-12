# System Administrator Guide: Field Maintenance Management Suite
**Author:** Manus AI  
**Target System:** Frappe v16 / ERPNext (`erp.elmrkz.cloud`)  
**Repository:** [unclee919/Maintenance-Management](https://github.com/unclee919/Maintenance-Management)

---

## 1. Overview
This System Administrator Guide provides complete operational instructions for managing, configuring, and maintaining the custom **Field Maintenance Management** (FSM) application deployed on Frappe v16. The application integrates seamlessly with standard ERPNext modules while introducing advanced field service capabilities—all 100% configurable via Frappe Desk without hardcoding.

---

## 2. Zero-Hardcode Configuration via Frappe Desk
All operational rules, weights, and automation policies are managed globally through the **Maintenance Settings** Single DocType (`Maintenance Settings` in Frappe Desk). 

### Key Configuration Parameters:
| Setting Category | Field Name | Description | Default Value |
| :--- | :--- | :--- | :--- |
| **Weighted Assignment** | Criteria Child Table | Dynamic weights for Proximity, Skill, Availability, Workload, Performance, Zone, and Route (Total 100%). | Configurable |
| **Automation** | `auto_create_invoice` | Automatically generate Sales Invoice upon task completion. | `1` (Enabled) |
| **Automation** | `auto_create_stock_entry` | Automatically generate Stock Entry (Consumption) for spare parts. | `1` (Enabled) |
| **Service Fee** | `default_service_fee_item` | Default service item code appended to invoices. | `MAINT-SVC-01` |
| **Shift Control** | `enforce_shift_hours` | Hold orders created outside shift hours until technician shift starts. | `1` (Enabled) |
| **Emergency** | `allow_emergency_override` | Bypass shift and workload constraints for emergency dispatches. | `1` (Enabled) |
| **Notifications** | `enable_sms`, `enable_whatsapp` | Notification channel toggles for dispatch alerts. | Configurable |
| **Enterprise QC** | `enforce_checklist` | Require mandatory QC checklist completion before task sign-off. | `1` (Enabled) |
| **Enterprise QC** | `auto_replenish_van` | Automatically create Stock Transfer when van stock is low. | `1` (Enabled) |
| **Diamond Standards** | `enable_pm_engine` | Enable automated Preventive Maintenance (PM) schedule generator. | `1` (Enabled) |
| **Diamond Standards** | `require_manager_review` | Require manager sign-off before invoice generation. | `1` (Enabled) |

---

## 3. Maintenance & Operational Procedures

### Routine Bench Maintenance & Migrations
When pulling updates from the GitHub repository, execute the following commands on the server:
```bash
su - frappe
cd frappe-bench
bench --site erp.elmrkz.cloud pull
bench --site erp.elmrkz.cloud migrate
bench --site erp.elmrkz.cloud clear-cache
supervisorctl restart all
```

### Automated Cloud Backups
Automated database and file backups are configured in `site_config.json` with a 7-day retention policy:
```json
{
    "auto_backup": 1,
    "backup_include_files": 1,
    "backup_limit": 7
}
```
Admins can manually trigger an instant backup via:
```bash
bench --site erp.elmrkz.cloud backup --with-files
```

---

## 4. Troubleshooting Common Issues

1. **Desk Icon Not Visible:**
   * Go to **Workspace** in Frappe Desk, locate **Maintenance Management**, and ensure `Is Standard` is unchecked and `Public` is checked. Run `bench --site erp.elmrkz.cloud clear-cache`.
2. **Assignment Engine Fails to Find Technician:**
   * Verify that technician records exist in the **Field Technician** DocType, their status is set to `Available`, and their service zone matches the customer's zone.
3. **Shift Dispatch Holding Orders:**
   * Check the technician's `shift_start` and `shift_end` times in their Field Technician profile. If orders must bypass shifts, toggle off `enforce_shift_hours` in **Maintenance Settings**.

---
*End of Administrator Guide.*
