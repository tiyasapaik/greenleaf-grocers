# Technical Project Report: GreenLeaf Grocers Inventory & Sales Management System

**Author:** Tiyasa Paik  
**Program:** Python Developer Internship  
**Host Institution:** Unified Mentor Private Limited  
**Date:** November 2026  

---

## 1. Introduction & Background
GreenLeaf Grocers is a medium-sized retail grocery operation dealing with fresh produce, dairy, bakery goods, packaged grains, and daily essentials. Previously, inventory tracking was handled through manual registers and disjointed spreadsheets, resulting in stock-outs of high-velocity items, undetected spoilage of perishable goods, billing errors, and zero real-time visibility into sales performance.

This project delivers a centralized, web-based inventory and sales management platform built using Python and Django, backed by automated stock deduction, role-based security, and visual analytics dashboards.

---

## 2. System Architecture & Database Design
The database architecture follows Third Normal Form (3NF) principles:
- **`inventory_supplier`:** Stores verified vendors with contact and address details.
- **`inventory_product`:** Central catalog tracking unit price, available physical stock, reorder thresholds, and expiration dates.
- **`billing_sale`:** Records transactions with cashier attribution, timestamp, subtotal, discount applied, and final payable amount.
- **`billing_saleitem`:** Bridges sales with products, recording quantity sold, snapshot unit price, and subtotal.

Atomic database transactions (`transaction.atomic()`) ensure that billing transactions and stock deductions are coupled; if a transaction fails (e.g. insufficient stock), all state modifications are rolled back.

---

## 3. Key Technical Challenges & Solutions

### Challenge 1: Race Conditions in Stock Deduction
*Problem:* In high-volume point-of-sale environments, multiple cashiers could simultaneously bill the last unit of a product, resulting in negative stock.  
*Solution:* Implemented row-level database locking using Django's `select_for_update()` inside an atomic transaction block. The stock is locked during billing verification and deducted before commit.

### Challenge 2: Multi-Timeframe Analytics & Fast Aggregations
*Problem:* Aggregating hundreds of sales records with multiple line items dynamically across customizable date ranges can degrade dashboard responsiveness.  
*Solution:* Leveraged Pandas alongside Django ORM aggregation functions (`Sum`, `Count`). Data is aggregated at the query level before being visualized via Plotly's rendering engine.

### Challenge 3: Seamless Dual Database Portability
*Problem:* Fulfilling SQLite requirements for frictionless evaluation while supporting standard enterprise MySQL engines.  
*Solution:* Utilized Django's database-agnostic ORM. The application defaults to zero-setup SQLite while bundling an automated MySQL DDL/DML exporter (`seed_data.py -> greenleaf_grocers_mysql.sql`).

---

## 4. Analytical Findings from Seed Benchmark (151 Days, 636 Sales)
- **Top Performing Category:** Grains & Pulses and Dairy & Eggs account for over 52% of total grocery sales revenue.
- **Basket Size:** The average bill value is ₹485.60, with customer baskets containing between 2 to 4 distinct items.
- **Stock Turnover Velocity:** Perishable bakery and dairy items exhibit a turnover cycle under 6 days, necessitating strict adherence to the 15-day near-expiry warning system.
- **Discount Responsiveness:** Promotional discounts of 5% to 10% boosted basket sizes by an average of 1.4 items during weekend trading periods.

---

## 5. Verification & Testing
The system was verified against 12 automated unit test scenarios covering:
1. Product creation and attributes integrity
2. Low stock threshold alert triggering
3. Near-expiry 15-day calculation
4. Expired product identification
5. SaleItem subtotal arithmetic calculation
6. Multi-tier discount computation
7. Stock quantity decrement upon sale execution
8. Validation against negative or over-stock billing
9. Role-based URL protection for unauthenticated users
10. Cashier POS billing operational authorization
11. Cashier restriction from sensitive business analytics
12. Administrator report access privileges

**Result: 12/12 Tests Passed (100% Success Rate).**
