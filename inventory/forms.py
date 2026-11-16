from django import forms
from .models import Product, Supplier


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'unit_price', 'stock_qty', 'reorder_level', 'expiry_date', 'supplier', 'barcode']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product name'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'stock_qty': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional barcode'}),
        }

    def clean_unit_price(self):
        price = self.cleaned_data.get('unit_price')
        if price is not None and price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price

    def clean_stock_qty(self):
        qty = self.cleaned_data.get('stock_qty')
        if qty is not None and qty < 0:
            raise forms.ValidationError("Stock quantity cannot be negative.")
        return qty


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'phone', 'email', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label='Select CSV File',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )
