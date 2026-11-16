from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Count, Avg, F
from django.utils import timezone
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import csv
import datetime

from billing.models import Sale, SaleItem
from inventory.models import Product


def is_admin(user):
    return user.is_staff or user.is_superuser


@login_required
def reports_dashboard(request):
    if not is_admin(request.user):
        from django.contrib import messages
        messages.error(request, "Only admins can access reports.")
        from django.shortcuts import redirect
        return redirect('dashboard')

    # Date range filter
    end_date = timezone.now().date()
    start_date = end_date - datetime.timedelta(days=30)
    if request.GET.get('start'):
        try:
            start_date = datetime.date.fromisoformat(request.GET['start'])
        except ValueError:
            pass
    if request.GET.get('end'):
        try:
            end_date = datetime.date.fromisoformat(request.GET['end'])
        except ValueError:
            pass

    view_mode = request.GET.get('view', 'revenue')  # 'revenue' or 'quantity'

    sales_qs = Sale.objects.filter(sale_date__range=[start_date, end_date])
    items_qs = SaleItem.objects.filter(sale__sale_date__range=[start_date, end_date])

    # ── KPIs ────────────────────────────────────────────────────────────────────
    total_revenue = sales_qs.aggregate(t=Sum('final_amount'))['t'] or 0
    total_bills = sales_qs.count()
    avg_bill = round(float(total_revenue) / total_bills, 2) if total_bills else 0
    low_stock_count = sum(1 for p in Product.objects.all() if p.is_low_stock)
    total_products = Product.objects.count()
    top_category = (
        items_qs.values('product__category')
        .annotate(rev=Sum('subtotal'))
        .order_by('-rev')
        .first()
    )
    top_cat_name = top_category['product__category'] if top_category else 'N/A'
    top_cat_pct = round(float(top_category['rev']) / float(total_revenue) * 100, 1) if top_category and total_revenue else 0

    # ── Daily Revenue Chart ──────────────────────────────────────────────────────
    daily = (
        sales_qs.values('sale_date')
        .annotate(revenue=Sum('final_amount'), bills=Count('id'))
        .order_by('sale_date')
    )
    if daily:
        df_daily = pd.DataFrame(list(daily))
        df_daily['sale_date'] = pd.to_datetime(df_daily['sale_date'])
        y_col = 'revenue' if view_mode == 'revenue' else 'bills'
        y_label = 'Revenue (₹)' if view_mode == 'revenue' else 'Number of Bills'
        fig_daily = px.area(
            df_daily, x='sale_date', y=y_col,
            title=f'Daily {y_label} ({start_date} to {end_date})',
            labels={'sale_date': 'Date', y_col: y_label},
            color_discrete_sequence=['#2d6a4f']
        )
        fig_daily.update_layout(plot_bgcolor='white', paper_bgcolor='white', height=320)
        chart_daily = fig_daily.to_html(full_html=False, include_plotlyjs=False)
    else:
        chart_daily = "<p class='text-muted'>No sales data in this period.</p>"

    # ── Monthly Revenue Chart ───────────────────────────────────────────────────
    all_sales = Sale.objects.values('sale_date').annotate(revenue=Sum('final_amount'), bills=Count('id'))
    if all_sales:
        df_monthly = pd.DataFrame(list(all_sales))
        df_monthly['sale_date'] = pd.to_datetime(df_monthly['sale_date'])
        df_monthly['month'] = df_monthly['sale_date'].dt.to_period('M').astype(str)
        df_m = df_monthly.groupby('month').agg({'revenue': 'sum', 'bills': 'sum'}).reset_index()
        y_col = 'revenue' if view_mode == 'revenue' else 'bills'
        fig_monthly = px.bar(
            df_m, x='month', y=y_col,
            title='Monthly Sales Trend',
            labels={'month': 'Month', y_col: 'Revenue (₹)' if view_mode == 'revenue' else 'Bills'},
            color_discrete_sequence=['#52b788']
        )
        fig_monthly.update_layout(plot_bgcolor='white', paper_bgcolor='white', height=320)
        chart_monthly = fig_monthly.to_html(full_html=False, include_plotlyjs=False)
    else:
        chart_monthly = "<p class='text-muted'>No data available.</p>"

    # ── Top 10 Products ─────────────────────────────────────────────────────────
    top_products = (
        items_qs.values('product__name')
        .annotate(total_qty=Sum('quantity'), total_rev=Sum('subtotal'))
        .order_by('-total_rev')[:10]
    )
    if top_products:
        df_top = pd.DataFrame(list(top_products))
        y_col = 'total_rev' if view_mode == 'revenue' else 'total_qty'
        y_label = 'Revenue (₹)' if view_mode == 'revenue' else 'Units Sold'
        fig_top = px.bar(
            df_top.sort_values(y_col), x=y_col, y='product__name',
            orientation='h',
            title=f'Top 10 Products by {y_label}',
            labels={'product__name': 'Product', y_col: y_label},
            color_discrete_sequence=['#1b4332']
        )
        fig_top.update_layout(plot_bgcolor='white', paper_bgcolor='white', height=360, yaxis_title='')
        chart_top = fig_top.to_html(full_html=False, include_plotlyjs=False)
    else:
        chart_top = "<p class='text-muted'>No data.</p>"

    # ── Category Pie Chart ──────────────────────────────────────────────────────
    cat_data = (
        items_qs.values('product__category')
        .annotate(total_rev=Sum('subtotal'), total_qty=Sum('quantity'))
        .order_by('-total_rev')
    )
    if cat_data:
        df_cat = pd.DataFrame(list(cat_data))
        y_col = 'total_rev' if view_mode == 'revenue' else 'total_qty'
        fig_cat = px.pie(
            df_cat, names='product__category', values=y_col,
            title='Category-wise Sales Share',
            color_discrete_sequence=px.colors.sequential.Greens_r
        )
        fig_cat.update_layout(height=360, paper_bgcolor='white')
        chart_cat = fig_cat.to_html(full_html=False, include_plotlyjs=False)
    else:
        chart_cat = "<p class='text-muted'>No data.</p>"

    # ── Low Stock Report ────────────────────────────────────────────────────────
    low_stock = [p for p in Product.objects.select_related('supplier').all() if p.is_low_stock]

    # ── Expiry Report ───────────────────────────────────────────────────────────
    expiry_items = [p for p in Product.objects.all() if p.is_near_expiry or p.is_expired]

    # ── Slow Moving (no sales in 30 days) ──────────────────────────────────────
    cutoff = timezone.now().date() - datetime.timedelta(days=30)
    sold_ids = SaleItem.objects.filter(
        sale__sale_date__gte=cutoff
    ).values_list('product_id', flat=True).distinct()
    slow_moving = Product.objects.exclude(id__in=sold_ids).filter(stock_qty__gt=0)

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'view_mode': view_mode,
        'total_revenue': total_revenue,
        'total_bills': total_bills,
        'avg_bill': avg_bill,
        'low_stock_count': low_stock_count,
        'total_products': total_products,
        'top_cat_name': top_cat_name,
        'top_cat_pct': top_cat_pct,
        'chart_daily': chart_daily,
        'chart_monthly': chart_monthly,
        'chart_top': chart_top,
        'chart_cat': chart_cat,
        'low_stock': low_stock,
        'expiry_items': expiry_items,
        'slow_moving': slow_moving,
        'top_products': top_products,
    }
    return render(request, 'reports/reports_dashboard.html', context)


@login_required
def export_sales_csv(request):
    if not is_admin(request.user):
        from django.shortcuts import redirect
        return redirect('dashboard')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Sale ID', 'Date', 'Time', 'Cashier', 'Total', 'Discount %', 'Final Amount'])
    for s in Sale.objects.select_related('cashier').order_by('-sale_date'):
        writer.writerow([s.id, s.sale_date, s.sale_time, s.cashier.username,
                         s.total_amount, s.discount, s.final_amount])
    return response


@login_required
def export_low_stock_csv(request):
    if not is_admin(request.user):
        from django.shortcuts import redirect
        return redirect('dashboard')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="low_stock_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Product', 'Category', 'Stock Qty', 'Reorder Level', 'Supplier'])
    for p in Product.objects.select_related('supplier').all():
        if p.is_low_stock:
            writer.writerow([p.name, p.category, p.stock_qty, p.reorder_level,
                             p.supplier.name if p.supplier else ''])
    return response
