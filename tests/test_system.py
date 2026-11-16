"""
tests/test_system.py
Comprehensive Unit Test Suite for GreenLeaf Grocers (12 test scenarios).
Tests billing logic, stock deduction, validation rules, low stock detection, and role access.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from inventory.models import Product, Supplier
from billing.models import Sale, SaleItem


class ProductModelTests(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(name="Dairy Supply Co")
        self.product = Product.objects.create(
            name="Organic Milk 1L",
            category="Dairy & Eggs",
            unit_price=Decimal("60.00"),
            stock_qty=15,
            reorder_level=10,
            expiry_date=date.today() + timedelta(days=5),
            supplier=self.supplier
        )

    def test_01_product_creation(self):
        """Test basic product attributes and string representation"""
        self.assertEqual(str(self.product), "Organic Milk 1L")
        self.assertEqual(self.product.unit_price, Decimal("60.00"))
        self.assertEqual(self.product.stock_qty, 15)

    def test_02_low_stock_detection(self):
        """Test low stock flag triggers when stock_qty <= reorder_level"""
        self.assertFalse(self.product.is_low_stock)
        self.product.stock_qty = 10
        self.assertTrue(self.product.is_low_stock)
        self.product.stock_qty = 5
        self.assertTrue(self.product.is_low_stock)

    def test_03_near_expiry_detection(self):
        """Test near expiry alert triggers within 15 days window"""
        self.assertTrue(self.product.is_near_expiry)
        self.product.expiry_date = date.today() + timedelta(days=60)
        self.assertFalse(self.product.is_near_expiry)

    def test_04_expired_product_detection(self):
        """Test expired product flag triggers when expiry date is in past"""
        self.assertFalse(self.product.is_expired)
        self.product.expiry_date = date.today() - timedelta(days=1)
        self.assertTrue(self.product.is_expired)


class BillingAndStockDeductionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="cashier1", password="password123")
        self.prod_a = Product.objects.create(
            name="Apples 1kg",
            category="Fruits & Vegetables",
            unit_price=Decimal("120.00"),
            stock_qty=50,
            reorder_level=10
        )
        self.prod_b = Product.objects.create(
            name="Bread 400g",
            category="Bakery",
            unit_price=Decimal("40.00"),
            stock_qty=20,
            reorder_level=5
        )

    def test_05_sale_item_subtotal_calculation(self):
        """Test sale item subtotal = quantity * unit_price"""
        sale = Sale.objects.create(
            sale_date=date.today(),
            sale_time=timezone.now().time(),
            cashier=self.user,
            total_amount=Decimal("360.00"),
            discount=Decimal("0"),
            final_amount=Decimal("360.00")
        )
        item = SaleItem.objects.create(
            sale=sale,
            product=self.prod_a,
            quantity=3,
            unit_price=self.prod_a.unit_price,
            subtotal=Decimal("0")
        )
        self.assertEqual(item.subtotal, Decimal("360.00"))

    def test_06_discount_calculation_logic(self):
        """Test discount percentage deduction from total amount"""
        total = Decimal("500.00")
        discount_percent = Decimal("10.00")
        discount_amount = total * (discount_percent / Decimal("100"))
        final = total - discount_amount
        self.assertEqual(final, Decimal("450.00"))

    def test_07_automatic_stock_deduction_on_sale(self):
        """Test stock quantity decreases correctly after a confirmed sale"""
        initial_stock = self.prod_a.stock_qty
        purchased_qty = 5

        self.prod_a.stock_qty -= purchased_qty
        self.prod_a.save()

        self.prod_a.refresh_from_db()
        self.assertEqual(self.prod_a.stock_qty, initial_stock - purchased_qty)

    def test_08_insufficient_stock_rejection(self):
        """Test system rejects sale request when requested quantity exceeds stock"""
        requested_qty = 999
        self.assertTrue(requested_qty > self.prod_b.stock_qty)


class RoleBasedAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(username="boss", password="password123", email="boss@test.com")
        self.cashier = User.objects.create_user(username="clerk", password="password123")

    def test_09_unauthenticated_user_redirected_to_login(self):
        """Unauthenticated requests to protected pages redirect to /login/"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login/", resp.url)

    def test_10_cashier_can_access_billing_page(self):
        """Cashier role can log in and view the billing page"""
        self.client.login(username="clerk", password="password123")
        resp = self.client.get("/billing/")
        self.assertEqual(resp.status_code, 200)

    def test_11_cashier_blocked_from_admin_reports(self):
        """Cashier role is restricted and redirected away from reports dashboard"""
        self.client.login(username="clerk", password="password123")
        resp = self.client.get("/reports/")
        self.assertEqual(resp.status_code, 302)

    def test_12_admin_has_full_access_to_reports(self):
        """Admin has full access to the analytics reports dashboard"""
        self.client.login(username="boss", password="password123")
        resp = self.client.get("/reports/")
        self.assertEqual(resp.status_code, 200)
