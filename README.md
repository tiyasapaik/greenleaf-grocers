# 🌿 GreenLeaf Grocers — Inventory & Sales Management System with Analytics Dashboard

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Django%205.2-green.svg)](https://www.djangoproject.com/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%7C%20MySQL-orange.svg)](https://www.mysql.com/)
[![Tests](https://img.shields.io/badge/Unit%20Tests-12%20Passed-brightgreen.svg)]()
[![Status](https://img.shields.io/badge/Status-Complete%20%26%20Production%20Ready-success.svg)]()

**Student Name:** Tiyasa Paik  
**Program:** Python Developer Internship  
**Host Organization:** Unified Mentor Private Limited  
**Project Title:** Inventory & Sales Management System with Analytics Dashboard for GreenLeaf Grocers  

---

## 📌 Executive Summary
Small and medium-sized grocery stores frequently experience inventory losses, stock-outs of fast-moving items, overstocking of perishable items leading to expiry wastage, billing inaccuracies, and an inability to track cashier sales. 

**GreenLeaf Grocers** is a full-stack Python & Django web application designed to centralize store operations, automate point-of-sale (POS) billing with real-time stock deduction, trigger proactive low-stock and near-expiry alerts, and provide store owners with executive analytics and visual dashboards.

---

## 🌟 Key Features

### 1. 🔐 Role-Based Access Control (RBAC)
- **Admin (`admin` / `admin123`):** Full access to store overview, product CRUD, supplier management, CSV bulk import/export, sales history, and comprehensive analytics reports.
- **Cashier (`cashier` / `cashier123`):** Streamlined access dedicated to point-of-sale (POS) billing, cart management, customer receipt printing, and PDF receipt downloads. Protected against unauthorized access to reports.

### 2. 📦 Product & Inventory Management
- **Full CRUD Operations:** Add, update, view, and delete products with strict validation (rejection of negative prices and stock).
- **Automated Alerts:**
  - ⚠️ **Low Stock Alert:** Automatically triggered whenever `stock_qty <= reorder_level`.
  - 📅 **Near-Expiry Warning:** Proactively flags items expiring within 15 days.
  - ❌ **Expired Product Detection:** Flags expired inventory in real-time.
- **Search & Multi-Filters:** Live filtering by name, barcode, category, low stock, and expiry status.
- **CSV Data Transfer:** Bulk import products from CSV and export inventory catalogs to CSV.

### 3. 🧾 Automated Point-of-Sale (POS) Billing
- **Dynamic Search & Selection:** Instant product search with real-time in-stock availability.
- **Item-Level Stock Validation:** Prevents cashier from selling more than available physical inventory.
- **Automatic Stock Deduction:** Atomic database transaction ensures accurate stock deduction immediately upon sale confirmation.
- **Promotional Discount:** Real-time percentage discount calculation.
- **Receipts:** Built-in web receipt, direct browser printing, and **Downloadable PDF Receipt** generated via ReportLab.

### 4. 📊 Executive Analytics & Visual Reports
Powered by **Pandas** and **Plotly**:
- **Daily Sales Trend:** Interactive area chart showing daily revenue and bill counts over a customizable date range.
- **Monthly Revenue:** Bar chart comparing monthly revenue performance over time.
- **Top 10 Selling Products:** Switchable views by **Revenue (₹)** or **Quantity Sold**.
- **Category Sales Distribution:** Donut/pie chart illustrating category contributions.
- **Slow-Moving Inventory Report:** Identifies products with zero sales in the last 30 days.
- **Key Performance Indicators (KPIs):** Total Revenue, Average Bill Value, Stock Turnover, Low Stock Count, Top Category Share (%).

---

## 🗄️ Database Architecture & Schema

The application implements a fully normalized relational schema:

```
┌─────────────────────────┐          ┌──────────────────────────┐
│   inventory_supplier    │          │        auth_user         │
├─────────────────────────┤          ├──────────────────────────┤
│ id (PK)                 │          │ id (PK)                  │
│ name                    │          │ username                 │
│ phone, email, address   │          │ password (hashed)        │
└────────────┬────────────┘          │ is_staff (Role flag)     │
             │ 1                     └─────────────┬────────────┘
             │                                     │ 1
             │ M                                   │
┌────────────┴────────────┐                        │ M
│    inventory_product    │          ┌─────────────┴────────────┐
├─────────────────────────┤          │       billing_sale       │
│ id (PK)                 │          ├──────────────────────────┤
│ name, category          │          │ id (PK)                  │
│ unit_price, stock_qty   │          │ sale_date, sale_time     │
│ reorder_level           │          │ cashier_id (FK)          │
│ expiry_date, barcode    │          │ total_amount, discount   │
│ supplier_id (FK)        │          │ final_amount             │
└────────────┬────────────┘          └─────────────┬────────────┘
             │ 1                                   │ 1
             │                                     │
             │ M                                   │ M
             │        ┌────────────────────────────┘
             │        │
             ▼        ▼
┌───────────────────────────────────┐
│         billing_saleitem          │
├───────────────────────────────────┤
│ id (PK)                           │
│ sale_id (FK)                      │
│ product_id (FK)                   │
│ quantity, unit_price, subtotal    │
└───────────────────────────────────┘
```

---

## 💻 Tech Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | Python 3.11 + Django 5.2 |
| **Relational Database** | SQLite (Default) / MySQL (XAMPP / Workbench Compatible) |
| **Analytics & Data Processing** | Pandas, NumPy |
| **Data Visualization** | Plotly Interactive Charts |
| **PDF Generation** | ReportLab |
| **Frontend UI** | HTML5, CSS3, Bootstrap 5, Bootstrap Icons |
| **Testing** | Django TestCase (12 Automated Tests) |

---

## 🚀 Installation & Setup Guide

### 1. Clone the Repository
```bash
git clone https://github.com/tiyasapaik/greenleaf-grocers.git
cd greenleaf-grocers
```

### 2. Create and Activate Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Apply Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Seed Database (59 Products & 636 Sales Transactions)
```bash
python seed_data.py
```
> This script also exports the full MySQL script `greenleaf_grocers_mysql.sql`.

### 6. Run the Application
```bash
python manage.py runserver
```
Open your browser and navigate to: **`http://127.0.0.1:8000/`**

---

## 🔑 Login Credentials

| Role | Username | Password | Purpose |
|:---|:---|:---|:---|
| **Admin / Store Manager** | `admin` | `admin123` | Full administrative control & analytics |
| **Cashier / POS Clerk** | `cashier` | `cashier123` | Fast billing, sales entry & receipt printing |

---

## 🧪 Automated Unit Test Suite

The project includes **12 automated unit tests** verifying model validation, stock deduction, discount logic, and security:

```bash
python manage.py test tests
```

### Test Results:
```text
Creating test database for alias 'default'...
............
----------------------------------------------------------------------
Ran 12 tests in 6.170s

OK
Destroying test database for alias 'default'...
```

---

## 🐬 MySQL Database Compatibility

The project includes **`greenleaf_grocers_mysql.sql`**, a complete, ready-to-import MySQL dump file.
To import into MySQL Workbench or phpMyAdmin:
```sql
CREATE DATABASE greenleaf_db;
USE greenleaf_db;
SOURCE greenleaf_grocers_mysql.sql;
```

---

## 📄 Submission Details
- **Intern:** Tiyasa Paik
- **Host Institution:** Unified Mentor Private Limited
- **Submission Scope:** Complete Source Code, Database Seed Scripts, 12 Unit Tests, Analytics Dashboard, and Technical Report.
