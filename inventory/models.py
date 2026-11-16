from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Supplier(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('Fruits & Vegetables', 'Fruits & Vegetables'),
        ('Dairy & Eggs', 'Dairy & Eggs'),
        ('Bakery', 'Bakery'),
        ('Meat & Seafood', 'Meat & Seafood'),
        ('Beverages', 'Beverages'),
        ('Snacks & Confectionery', 'Snacks & Confectionery'),
        ('Grains & Pulses', 'Grains & Pulses'),
        ('Spices & Condiments', 'Spices & Condiments'),
        ('Frozen Foods', 'Frozen Foods'),
        ('Personal Care', 'Personal Care'),
        ('Household', 'Household'),
        ('Other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_qty = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=10)
    expiry_date = models.DateField(null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    barcode = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.stock_qty <= self.reorder_level

    @property
    def is_near_expiry(self):
        if self.expiry_date:
            days_left = (self.expiry_date - timezone.now().date()).days
            return 0 <= days_left <= 15
        return False

    @property
    def is_expired(self):
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False

    class Meta:
        ordering = ['name']
