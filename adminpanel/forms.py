from django import forms
from myapp.models import Product,Category,ProductVariant
from order.models import Order
from payment.models import PaymentOrder
from cart.models import Coupon
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 
            'price_initial', 
            'category', 
            'description', 
            'image', 
            'is_popular', 
            'is_featured', 
            'is_sale', 
            'sale_price', 
            'date', 
            'rating', 
            'is_blocked',
            'base_product_detail'
        ]

    # Custom validation for the fields can be added here if needed
    def clean_price(self):
        price = self.cleaned_data['price']
        if price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price

    def clean_sale_price(self):
        sale_price = self.cleaned_data['sale_price']
        if sale_price < 0:
            raise forms.ValidationError("Sale price cannot be negative.")
        return sale_price
    
class OrderStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']  # Only allow status updates
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'})
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description','image']

class PaidOrderStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = PaymentOrder
        fields = ['status']  # Only allow status updates
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'})
        }

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'discount_type', 'discount_value', 'expiration_date', 'usage_limit', 'is_active']
        widgets = {
            'expiration_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['name', 'price', 'color', 'size', 'stock_quantity', 'image']