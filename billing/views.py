from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db import transaction
import json
import io
from decimal import Decimal

from inventory.models import Product
from .models import Sale, SaleItem


@login_required
def billing_page(request):
    """Main billing / POS page"""
    categories = Product.CATEGORY_CHOICES
    return render(request, 'billing/billing.html', {'categories': categories})


@login_required
def search_products(request):
    """AJAX: search products for the billing page"""
    q = request.GET.get('q', '')
    products = Product.objects.filter(
        name__icontains=q, stock_qty__gt=0
    ).values('id', 'name', 'unit_price', 'stock_qty', 'category')[:20]
    return JsonResponse({'products': list(products)})


@login_required
def create_sale(request):
    """AJAX POST: submit a completed bill"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    items = data.get('items', [])
    discount = Decimal(str(data.get('discount', 0)))

    if not items:
        return JsonResponse({'error': 'No items in bill'}, status=400)

    if discount < 0 or discount > 100:
        return JsonResponse({'error': 'Discount must be between 0 and 100'}, status=400)

    with transaction.atomic():
        total = Decimal('0')
        sale_items_to_create = []

        for item in items:
            try:
                product = Product.objects.select_for_update().get(pk=item['product_id'])
            except Product.DoesNotExist:
                return JsonResponse({'error': f"Product ID {item['product_id']} not found"}, status=404)

            qty = int(item['quantity'])
            if qty <= 0:
                return JsonResponse({'error': f"Invalid quantity for {product.name}"}, status=400)
            if qty > product.stock_qty:
                return JsonResponse({
                    'error': f"Insufficient stock for '{product.name}'. Available: {product.stock_qty}, Requested: {qty}"
                }, status=400)

            subtotal = Decimal(str(product.unit_price)) * qty
            total += subtotal
            sale_items_to_create.append((product, qty, product.unit_price, subtotal))

        discount_amount = total * discount / 100
        final_amount = total - discount_amount

        now = timezone.now()
        sale = Sale.objects.create(
            sale_date=now.date(),
            sale_time=now.time(),
            cashier=request.user,
            total_amount=total,
            discount=discount,
            final_amount=final_amount,
        )

        for product, qty, price, subtotal in sale_items_to_create:
            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=qty,
                unit_price=price,
                subtotal=subtotal,
            )
            # Deduct stock
            product.stock_qty -= qty
            product.save()

    return JsonResponse({
        'success': True,
        'sale_id': sale.id,
        'total': float(total),
        'discount': float(discount),
        'final_amount': float(final_amount),
        'redirect': f'/billing/receipt/{sale.id}/'
    })


@login_required
def receipt(request, sale_id):
    """Bill receipt page"""
    sale = get_object_or_404(Sale.objects.select_related('cashier'), pk=sale_id)
    items = sale.items.select_related('product').all()
    return render(request, 'billing/receipt.html', {'sale': sale, 'items': items})


@login_required
def receipt_pdf(request, sale_id):
    """Download receipt as PDF"""
    from reportlab.pagesizes import A5
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER

    sale = get_object_or_404(Sale, pk=sale_id)
    items = sale.items.select_related('product').all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A5, leftMargin=1.5*cm, rightMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    story = []

    center = ParagraphStyle('center', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10)
    story.append(Paragraph("<b>GreenLeaf Grocers</b>", ParagraphStyle('title', parent=styles['Normal'],
                            alignment=TA_CENTER, fontSize=14, spaceAfter=4)))
    story.append(Paragraph("Fresh Produce · Groceries · Daily Essentials", center))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"Receipt #: {sale.id}", center))
    story.append(Paragraph(f"Date: {sale.sale_date}  |  Time: {sale.sale_time.strftime('%H:%M')}", center))
    story.append(Paragraph(f"Cashier: {sale.cashier.get_full_name() or sale.cashier.username}", center))
    story.append(Spacer(1, 0.3*cm))

    data = [['Item', 'Qty', 'Price', 'Subtotal']]
    for item in items:
        data.append([item.product.name, str(item.quantity),
                     f"₹{item.unit_price}", f"₹{item.subtotal}"])
    data.append(['', '', 'Total', f"₹{sale.total_amount}"])
    if sale.discount > 0:
        data.append(['', '', f'Discount ({sale.discount}%)', f'-₹{sale.total_amount * sale.discount / 100:.2f}'])
    data.append(['', '', 'AMOUNT DUE', f"₹{sale.final_amount}"])

    t = Table(data, colWidths=[7*cm, 1.5*cm, 2.5*cm, 2.5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -2), 0.3, colors.lightgrey),
        ('FONTNAME', (2, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d8f3dc')),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Thank you for shopping at GreenLeaf Grocers!", center))

    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{sale.id}.pdf"'
    return response


@login_required
def sale_list(request):
    """List all sales — admin only"""
    sales = Sale.objects.select_related('cashier').order_by('-sale_date', '-sale_time')
    return render(request, 'billing/sale_list.html', {'sales': sales})
