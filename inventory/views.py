from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q
from django.utils import timezone
import csv
import io

from .models import Product, Supplier
from .forms import ProductForm, SupplierForm, CSVImportForm


def is_admin(user):
    return user.is_staff or user.is_superuser


@login_required
def dashboard(request):
    from billing.models import Sale, SaleItem
    from django.db.models import Sum, Count
    import datetime

    today = timezone.now().date()
    total_products = Product.objects.count()
    

    # Count products where stock <= reorder_level
    low_stock_count = sum(1 for p in Product.objects.all() if p.is_low_stock)
    near_expiry_count = sum(1 for p in Product.objects.all() if p.is_near_expiry)
    expired_count = sum(1 for p in Product.objects.all() if p.is_expired)

    today_sales = Sale.objects.filter(sale_date=today)
    today_revenue = today_sales.aggregate(total=Sum('final_amount'))['total'] or 0
    today_bills = today_sales.count()

    recent_sales = Sale.objects.select_related('cashier').order_by('-sale_date', '-sale_time')[:8]
    low_stock_products = [p for p in Product.objects.all() if p.is_low_stock][:8]
    near_expiry_products = [p for p in Product.objects.all() if p.is_near_expiry][:5]

    context = {
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'near_expiry_count': near_expiry_count,
        'expired_count': expired_count,
        'today_revenue': today_revenue,
        'today_bills': today_bills,
        'recent_sales': recent_sales,
        'low_stock_products': low_stock_products,
        'near_expiry_products': near_expiry_products,
        'today': today,
    }
    return render(request, 'dashboard.html', context)


@login_required
def product_list(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    stock_filter = request.GET.get('stock', '')

    products = Product.objects.select_related('supplier').all()

    if query:
        products = products.filter(Q(name__icontains=query) | Q(barcode__icontains=query))
    if category:
        products = products.filter(category=category)
    if stock_filter == 'low':
        products = [p for p in products if p.is_low_stock]
    elif stock_filter == 'expiry':
        products = [p for p in products if p.is_near_expiry]

    categories = Product.CATEGORY_CHOICES

    context = {
        'products': products,
        'query': query,
        'category': category,
        'stock_filter': stock_filter,
        'categories': categories,
        'is_admin': is_admin(request.user),
    }
    return render(request, 'inventory/product_list.html', context)


@login_required
def product_add(request):
    if not is_admin(request.user):
        messages.error(request, "Only admins can add products.")
        return redirect('product_list')

    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Product '{form.cleaned_data['name']}' added successfully!")
            return redirect('product_list')
    else:
        form = ProductForm()

    return render(request, 'inventory/product_form.html', {'form': form, 'action': 'Add Product'})


@login_required
def product_edit(request, pk):
    if not is_admin(request.user):
        messages.error(request, "Only admins can edit products.")
        return redirect('product_list')

    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"Product '{product.name}' updated successfully!")
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)

    return render(request, 'inventory/product_form.html', {'form': form, 'action': 'Edit Product', 'product': product})


@login_required
def product_delete(request, pk):
    if not is_admin(request.user):
        messages.error(request, "Only admins can delete products.")
        return redirect('product_list')

    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f"Product '{name}' deleted.")
        return redirect('product_list')

    return render(request, 'inventory/product_confirm_delete.html', {'product': product})


@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'inventory/product_detail.html', {'product': product})


@login_required
def supplier_list(request):
    if not is_admin(request.user):
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    suppliers = Supplier.objects.all()
    return render(request, 'inventory/supplier_list.html', {'suppliers': suppliers})


@login_required
def supplier_add(request):
    if not is_admin(request.user):
        return redirect('dashboard')
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Supplier added successfully!")
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'inventory/supplier_form.html', {'form': form, 'action': 'Add Supplier'})


@login_required
def import_products_csv(request):
    if not is_admin(request.user):
        return redirect('dashboard')

    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            decoded = csv_file.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(decoded))
            count = 0
            errors = []
            for i, row in enumerate(reader, 1):
                try:
                    name = row.get('name', '').strip()
                    if not name:
                        continue
                    category = row.get('category', 'Other').strip()
                    if category not in [c[0] for c in Product.CATEGORY_CHOICES]:
                        category = 'Other'
                    price = float(row.get('unit_price', 0))
                    stock = int(row.get('stock_qty', 0))
                    reorder = int(row.get('reorder_level', 10))
                    if price < 0 or stock < 0:
                        errors.append(f"Row {i}: negative values skipped.")
                        continue
                    Product.objects.update_or_create(
                        name=name,
                        defaults={
                            'category': category,
                            'unit_price': price,
                            'stock_qty': stock,
                            'reorder_level': reorder,
                        }
                    )
                    count += 1
                except Exception as e:
                    errors.append(f"Row {i}: {e}")

            if errors:
                for err in errors[:5]:
                    messages.warning(request, err)
            messages.success(request, f"{count} products imported successfully!")
            return redirect('product_list')
    else:
        form = CSVImportForm()

    return render(request, 'inventory/import_csv.html', {'form': form})


@login_required
def export_products_csv(request):
    if not is_admin(request.user):
        return redirect('dashboard')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['name', 'category', 'unit_price', 'stock_qty', 'reorder_level', 'expiry_date', 'barcode'])
    for p in Product.objects.all():
        writer.writerow([p.name, p.category, p.unit_price, p.stock_qty, p.reorder_level,
                         p.expiry_date or '', p.barcode])
    return response



