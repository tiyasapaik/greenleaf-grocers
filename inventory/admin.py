from django.contrib import admin
from .models import Product, Supplier

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'unit_price', 'stock_qty', 'reorder_level', 'expiry_date', 'is_low_stock']
    list_filter = ['category', 'supplier']
    search_fields = ['name', 'barcode']
    list_editable = ['stock_qty', 'unit_price']

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email']
    search_fields = ['name']
