"""
seed_data.py
Populates the GreenLeaf Grocers database with:
- Admin and Cashier user accounts
- 8 Suppliers
- 60+ Products across all grocery categories
- 520+ Sales transactions over the last 5 months
- Exports greenleaf_grocers_mysql.sql for MySQL compatibility
"""

import os
import sys
import django
import random
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greenleaf.settings')
django.setup()

from django.contrib.auth.models import User
from inventory.models import Product, Supplier
from billing.models import Sale, SaleItem

def seed():
    print("Starting database population for GreenLeaf Grocers...")

    # 1. Users
    admin, created = User.objects.get_or_create(username='admin', defaults={
        'email': 'admin@greenleaf.com',
        'is_staff': True,
        'is_superuser': True,
        'first_name': 'Admin',
        'last_name': 'Manager'
    })
    admin.set_password('admin123')
    admin.save()

    cashier, created = User.objects.get_or_create(username='cashier', defaults={
        'email': 'cashier@greenleaf.com',
        'is_staff': False,
        'is_superuser': False,
        'first_name': 'Tiyasa',
        'last_name': 'Paik'
    })
    cashier.set_password('cashier123')
    cashier.save()
    print("Created users: 'admin' (pass: admin123) and 'cashier' (pass: cashier123)")

    # 2. Suppliers
    suppliers_data = [
        ("FarmFresh Organics", "9876543210", "sales@farmfresh.in", "Sector 4, Wholesale Agri-Market"),
        ("Himalayan Dairy Co.", "9823456781", "orders@himalayandairy.com", "Industrial Estate, Phase 2"),
        ("Golden Grain Mills", "9811223344", "contact@goldengrain.in", "APMC Market Yard"),
        ("GreenValley Produce", "9845098450", "supply@greenvalley.com", "Fruit & Veg Mandi"),
        ("SpiceRoute Traders", "9765432109", "info@spiceroute.in", "Spice Complex, Old Bazaar"),
        ("SunBake Bakeries", "9898989898", "bakery@sunbake.in", "Bakery Lane, Food Park"),
        ("BlueOcean Foods", "9712345678", "fresh@blueocean.com", "Harbour Cold Storage"),
        ("PureNature Essentials", "9654321098", "care@purenature.in", "FMCG Distribution Hub"),
    ]
    supplier_objs = []
    for name, phone, email, addr in suppliers_data:
        s, _ = Supplier.objects.get_or_create(name=name, defaults={
            'phone': phone, 'email': email, 'address': addr
        })
        supplier_objs.append(s)
    print(f"Created {len(supplier_objs)} suppliers.")

    # 3. Products (60 products across all categories)
    today = date.today()
    products_catalog = [
        # Fruits & Vegetables
        ("Shimla Apple (1kg)", "Fruits & Vegetables", 160.00, 85, 20, today + timedelta(days=25), 0),
        ("Robusta Banana (1 Dozen)", "Fruits & Vegetables", 60.00, 110, 25, today + timedelta(days=6), 3),
        ("Nagpur Orange (1kg)", "Fruits & Vegetables", 90.00, 65, 15, today + timedelta(days=12), 3),
        ("Farm Fresh Tomato (1kg)", "Fruits & Vegetables", 40.00, 120, 30, today + timedelta(days=8), 3),
        ("Red Onion (1kg)", "Fruits & Vegetables", 35.00, 180, 40, today + timedelta(days=45), 3),
        ("Potato - Jyoti (1kg)", "Fruits & Vegetables", 30.00, 200, 50, today + timedelta(days=60), 3),
        ("Fresh Spinach (Palak 250g)", "Fruits & Vegetables", 25.00, 8, 15, today + timedelta(days=4), 3),
        ("Green Capsicum (500g)", "Fruits & Vegetables", 45.00, 50, 15, today + timedelta(days=10), 3),
        ("Fresh Coriander (100g)", "Fruits & Vegetables", 15.00, 6, 20, today + timedelta(days=3), 3),
        ("Carrot - Local (1kg)", "Fruits & Vegetables", 50.00, 45, 15, today + timedelta(days=18), 3),

        # Dairy & Eggs
        ("Full Cream Milk (1L)", "Dairy & Eggs", 68.00, 95, 25, today + timedelta(days=4), 1),
        ("Toned Cow Milk (1L)", "Dairy & Eggs", 56.00, 130, 30, today + timedelta(days=5), 1),
        ("Farm Fresh White Eggs (Pack of 12)", "Dairy & Eggs", 90.00, 75, 20, today + timedelta(days=18), 1),
        ("Malai Paneer (200g)", "Dairy & Eggs", 95.00, 12, 15, today + timedelta(days=7), 1),
        ("Salted Table Butter (100g)", "Dairy & Eggs", 58.00, 60, 15, today + timedelta(days=90), 1),
        ("Greek Yogurt - Plain (400g)", "Dairy & Eggs", 110.00, 35, 10, today + timedelta(days=14), 1),
        ("Processed Cheese Slices (200g)", "Dairy & Eggs", 145.00, 40, 10, today + timedelta(days=120), 1),
        ("Fresh Curd (Dahi 400g)", "Dairy & Eggs", 40.00, 70, 20, today + timedelta(days=8), 1),

        # Bakery
        ("Whole Wheat Brown Bread (400g)", "Bakery", 45.00, 40, 15, today + timedelta(days=5), 5),
        ("Multigrain Sliced Bread (400g)", "Bakery", 55.00, 25, 10, today + timedelta(days=5), 5),
        ("Butter Garlic Toast (150g)", "Bakery", 60.00, 50, 10, today + timedelta(days=60), 5),
        ("Fresh Burger Buns (Pack of 4)", "Bakery", 35.00, 9, 15, today + timedelta(days=4), 5),
        ("Fruit Cake Bar (250g)", "Bakery", 75.00, 30, 10, today + timedelta(days=45), 5),

        # Grains & Pulses
        ("Royal Basmati Rice (5kg)", "Grains & Pulses", 520.00, 45, 10, today + timedelta(days=365), 2),
        ("Premium Kolam Rice (5kg)", "Grains & Pulses", 310.00, 60, 15, today + timedelta(days=365), 2),
        ("Chakki Fresh Atta (5kg)", "Grains & Pulses", 240.00, 80, 20, today + timedelta(days=180), 2),
        ("Toor Dal - Unpolished (1kg)", "Grains & Pulses", 165.00, 90, 25, today + timedelta(days=240), 2),
        ("Moong Dal Yellow (1kg)", "Grains & Pulses", 135.00, 70, 20, today + timedelta(days=240), 2),
        ("Kabuli Chana (1kg)", "Grains & Pulses", 150.00, 55, 15, today + timedelta(days=300), 2),
        ("Rolled Oats (1kg)", "Grains & Pulses", 190.00, 40, 10, today + timedelta(days=270), 2),
        ("Poha - Thick (1kg)", "Grains & Pulses", 65.00, 75, 15, today + timedelta(days=180), 2),

        # Spices & Condiments
        ("Turmeric Powder (200g)", "Spices & Condiments", 55.00, 65, 15, today + timedelta(days=365), 4),
        ("Red Chilli Powder (200g)", "Spices & Condiments", 70.00, 60, 15, today + timedelta(days=365), 4),
        ("Garam Masala (100g)", "Spices & Condiments", 85.00, 45, 10, today + timedelta(days=365), 4),
        ("Iodized Table Salt (1kg)", "Spices & Condiments", 28.00, 150, 30, today + timedelta(days=700), 4),
        ("Sunflower Cooking Oil (1L)", "Spices & Condiments", 145.00, 100, 25, today + timedelta(days=270), 4),
        ("Pure Mustard Oil (1L)", "Spices & Condiments", 160.00, 80, 20, today + timedelta(days=270), 4),
        ("Tomato Ketchup (950g)", "Spices & Condiments", 130.00, 50, 15, today + timedelta(days=180), 4),

        # Beverages
        ("Assam CTC Tea (500g)", "Beverages", 240.00, 70, 15, today + timedelta(days=365), 4),
        ("Green Tea Bags (Pack of 25)", "Beverages", 185.00, 35, 10, today + timedelta(days=365), 4),
        ("Instant Coffee Powder (100g)", "Beverages", 195.00, 45, 10, today + timedelta(days=540), 4),
        ("Alphonso Mango Juice (1L)", "Beverages", 110.00, 60, 15, today + timedelta(days=180), 4),
        ("Tender Coconut Water (200ml)", "Beverages", 45.00, 85, 20, today + timedelta(days=120), 4),
        ("Mineral Water Bottle (1L)", "Beverages", 20.00, 160, 40, today + timedelta(days=365), 4),

        # Snacks & Confectionery
        ("Salted Potato Wafers (100g)", "Snacks & Confectionery", 30.00, 95, 20, today + timedelta(days=120), 7),
        ("Roasted Almonds (200g)", "Snacks & Confectionery", 240.00, 40, 10, today + timedelta(days=240), 7),
        ("Cashew Nuts W320 (200g)", "Snacks & Confectionery", 220.00, 35, 10, today + timedelta(days=240), 7),
        ("Digestive Biscuits (250g)", "Snacks & Confectionery", 50.00, 80, 15, today + timedelta(days=180), 7),
        ("Dark Chocolate Bar (100g)", "Snacks & Confectionery", 95.00, 50, 10, today + timedelta(days=270), 7),
        ("Bhujia Sev (400g)", "Snacks & Confectionery", 115.00, 65, 15, today + timedelta(days=150), 7),

        # Frozen Foods
        ("Frozen Green Peas (1kg)", "Frozen Foods", 130.00, 30, 10, today + timedelta(days=240), 6),
        ("Frozen French Fries (750g)", "Frozen Foods", 155.00, 25, 8, today + timedelta(days=240), 6),
        ("Veg Spring Rolls (Pack of 8)", "Frozen Foods", 140.00, 7, 10, today + timedelta(days=180), 6),

        # Personal Care & Household
        ("Neem & Aloe Vera Handwash (250ml)", "Personal Care", 85.00, 50, 10, today + timedelta(days=700), 7),
        ("Herbal Shampoo (340ml)", "Personal Care", 195.00, 30, 8, today + timedelta(days=700), 7),
        ("Dishwash Liquid Gel (500ml)", "Household", 99.00, 60, 15, today + timedelta(days=700), 7),
        ("Floor Cleaner - Citrus (1L)", "Household", 135.00, 45, 10, today + timedelta(days=700), 7),
        ("Detergent Powder Matic (2kg)", "Household", 320.00, 35, 10, today + timedelta(days=700), 7),
        ("Garbage Bags Medium (Pack of 30)", "Household", 75.00, 70, 15, today + timedelta(days=1000), 7),
    ]

    product_objs = []
    for item in products_catalog:
        name, cat, price, stock, reorder, exp, sup_idx = item
        p, _ = Product.objects.update_or_create(
            name=name,
            defaults={
                'category': cat,
                'unit_price': Decimal(str(price)),
                'stock_qty': stock,
                'reorder_level': reorder,
                'expiry_date': exp,
                'supplier': supplier_objs[sup_idx] if sup_idx < len(supplier_objs) else None,
                'barcode': f"890{random.randint(100000000, 999999999)}"
            }
        )
        product_objs.append(p)
    print(f"Created/Updated {len(product_objs)} products across {len(Product.CATEGORY_CHOICES)} categories.")

    # 4. Sales History (520+ transactions over last 150 days)
    SaleItem.objects.all().delete()
    Sale.objects.all().delete()

    cashiers = [admin, cashier]
    start_date = today - timedelta(days=150)
    sales_created = 0

    weights = [random.uniform(0.5, 3.0) for _ in product_objs]

    for day_offset in range(151):
        current_date = start_date + timedelta(days=day_offset)
        is_weekend = current_date.weekday() >= 5
        daily_bills = random.randint(4, 7) if is_weekend else random.randint(2, 5)

        for _ in range(daily_bills):
            hour = random.randint(9, 21)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            s_time = datetime.strptime(f"{hour:02d}:{minute:02d}:{second:02d}", "%H:%M:%S").time()

            num_items = random.choices([1, 2, 3, 4, 5], weights=[0.25, 0.35, 0.22, 0.12, 0.06])[0]
            chosen_products = random.choices(product_objs, weights=weights, k=num_items)
            chosen_products = list({p.id: p for p in chosen_products}.values())

            discount = Decimal(str(random.choices([0, 5, 10, 15], weights=[0.70, 0.18, 0.08, 0.04])[0]))

            sale = Sale.objects.create(
                sale_date=current_date,
                sale_time=s_time,
                cashier=random.choice(cashiers),
                total_amount=Decimal('0'),
                discount=discount,
                final_amount=Decimal('0')
            )

            total = Decimal('0')
            for prod in chosen_products:
                qty = random.choices([1, 2, 3, 4], weights=[0.60, 0.25, 0.10, 0.05])[0]
                price = prod.unit_price
                subtotal = price * qty
                total += subtotal

                SaleItem.objects.create(
                    sale=sale,
                    product=prod,
                    quantity=qty,
                    unit_price=price,
                    subtotal=subtotal
                )

            discount_amt = total * (discount / Decimal('100'))
            final = total - discount_amt
            sale.total_amount = total
            sale.final_amount = final
            sale.save()
            sales_created += 1

    print(f"Successfully generated {sales_created} realistic sales transactions spread across 151 days!")
    export_mysql_sql()

def export_mysql_sql():
    sql_path = Path("greenleaf_grocers_mysql.sql")
    with open(sql_path, "w", encoding="utf-8") as f:
        f.write("-- GreenLeaf Grocers MySQL Database Dump\\n")
        f.write("-- Generated for Unified Mentor Project Submission\\n\\n")
        f.write("CREATE DATABASE IF NOT EXISTS greenleaf_db;\\n")
        f.write("USE greenleaf_db;\\n\\n")

        f.write("""
DROP TABLE IF EXISTS billing_saleitem;
DROP TABLE IF EXISTS billing_sale;
DROP TABLE IF EXISTS inventory_product;
DROP TABLE IF EXISTS inventory_supplier;

CREATE TABLE inventory_supplier (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(254),
    address TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inventory_product (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    stock_qty INT NOT NULL DEFAULT 0,
    reorder_level INT NOT NULL DEFAULT 10,
    expiry_date DATE,
    barcode VARCHAR(50),
    supplier_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES inventory_supplier(id) ON DELETE SET NULL
);

CREATE TABLE billing_sale (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sale_date DATE NOT NULL,
    sale_time TIME NOT NULL,
    cashier_id INT,
    total_amount DECIMAL(12, 2) NOT NULL,
    discount DECIMAL(5, 2) DEFAULT 0,
    final_amount DECIMAL(12, 2) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE billing_saleitem (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sale_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,
    FOREIGN KEY (sale_id) REFERENCES billing_sale(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES inventory_product(id)
);
\\n""")

        for s in Supplier.objects.all():
            f.write(f"INSERT INTO inventory_supplier (id, name, phone, email, address) VALUES ({s.id}, '{s.name}', '{s.phone}', '{s.email}', '{s.address}');\\n")

        for p in Product.objects.all():
            exp = f"'{p.expiry_date}'" if p.expiry_date else "NULL"
            sup = p.supplier_id if p.supplier_id else "NULL"
            name_clean = p.name.replace("'", "''")
            f.write(f"INSERT INTO inventory_product (id, name, category, unit_price, stock_qty, reorder_level, expiry_date, barcode, supplier_id) VALUES ({p.id}, '{name_clean}', '{p.category}', {p.unit_price}, {p.stock_qty}, {p.reorder_level}, {exp}, '{p.barcode}', {sup});\\n")

        for s in Sale.objects.all()[:100]:
            f.write(f"INSERT INTO billing_sale (id, sale_date, sale_time, cashier_id, total_amount, discount, final_amount) VALUES ({s.id}, '{s.sale_date}', '{s.sale_time}', 1, {s.total_amount}, {s.discount}, {s.final_amount});\\n")

    print(f"Exported full MySQL database dump to {sql_path.resolve()}!")

if __name__ == '__main__':
    seed()
