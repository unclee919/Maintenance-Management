# API Integration & Developer Guide: Field Maintenance Management Suite
**Author:** Manus AI  
**Target System:** Frappe v16 / ERPNext (`erp.elmrkz.cloud`)  
**Repository:** [unclee919/Maintenance-Management](https://github.com/unclee919/Maintenance-Management)

---

## 1. Overview
This document outlines all custom REST API endpoints exposed by the **Maintenance Management** application on Frappe v16. These endpoints are designed for seamless integration with external automation tools like **n8n**, mobile portals, and customer self-service applications.

All endpoints require standard Frappe token authentication (`token apiKey:apiSecret` in the `Authorization` header) or active session cookies.

---

## 2. Core API Endpoints Reference

### 2.1 Technician Location & GPS Tracking
* **Endpoint:** `/api/method/maintenance_management.maintenance_management.api.update_technician_location`
* **Method:** `POST`
* **Parameters:**
  * `technician` (string): ID of the Field Technician.
  * `latitude` (float): Current GPS latitude.
  * `longitude` (float): Current GPS longitude.
  * `sales_order` (string, optional): Active sales order ID.
* **Response:** `{"status": "success", "log_id": "LOC-LOG-00012"}`

### 2.2 Shift & Order Dispatch Check
* **Endpoint:** `/api/method/maintenance_management.maintenance_management.api.check_technician_shift`
* **Method:** `POST`
* **Parameters:**
  * `technician` (string): ID of the technician.
* **Response:** `{"status": "active" | "held", "message": "..."}`

### 2.3 Technician-Initiated Orders
* **Endpoint:** `/api/method/maintenance_management.maintenance_management.api.create_technician_order`
* **Method:** `POST`
* **Parameters:**
  * `technician` (string): Technician ID.
  * `customer` (string): Customer name.
  * `problem_description` (string): Description of issue.
  * `latitude` (float): GPS latitude.
  * `longitude` (float): GPS longitude.
* **Response:** `{"status": "success", "sales_order": "SAL-ORD-00045"}`

### 2.4 Spare Parts Requests
* **Endpoint:** `/api/method/maintenance_management.maintenance_management.api.request_spare_parts`
* **Method:** `POST`
* **Parameters:**
  * `sales_order` (string): Maintenance order ID.
  * `technician` (string): Technician ID.
  * `items` (JSON list): `[{"item_code": "PART-01", "qty": 2}]`
* **Response:** `{"status": "success", "material_request": "MAT-REQ-00010"}`

### 2.5 Public Customer Tracking
* **Endpoint:** `/api/method/maintenance_management.maintenance_management.api.get_customer_tracking`
* **Method:** `GET` (Allow Guest)
* **Parameters:**
  * `sales_order` (string): Maintenance order ID.
* **Response:** Live technician GPS coordinates, ETA, status, and audit trail.

---
*End of API Integration Guide.*
