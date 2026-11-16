from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_dashboard, name='reports'),
    path('export/sales/', views.export_sales_csv, name='export_sales_csv'),
    path('export/low-stock/', views.export_low_stock_csv, name='export_low_stock_csv'),
]
