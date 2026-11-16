from django.urls import path
from . import views

urlpatterns = [
    path('', views.billing_page, name='billing'),
    path('search-products/', views.search_products, name='search_products'),
    path('create-sale/', views.create_sale, name='create_sale'),
    path('receipt/<int:sale_id>/', views.receipt, name='receipt'),
    path('receipt/<int:sale_id>/pdf/', views.receipt_pdf, name='receipt_pdf'),
    path('sales/', views.sale_list, name='sale_list'),
]
