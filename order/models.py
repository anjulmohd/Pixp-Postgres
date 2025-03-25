from django.db import models
from django.contrib.auth import get_user_model
from myapp.models import Product,ProductVariant
import uuid
import random
import string

User = get_user_model()


# Create your models here.
class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ("RETURN_REQUESTED", "Return Requested"),
        ("RETURN_APPROVED", "Return Approved"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order_unique_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    reason = models.TextField(blank=True, null=True)  # New field

    def save(self, *args, **kwargs):
        if not self.order_unique_id:
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            self.order_unique_id = f"ORD{(self.id or 1000) * 7}{random_part}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True) 
    return_requested = models.BooleanField(default=False)  # New field
    return_approved = models.BooleanField(default=False)  # New field
    reason = models.TextField(null=True, blank=True)  # New field for return reason

    def get_total_price(self):
        # Calculate total price based on product or variant
        if self.product_variant:
            return self.quantity * self.product_variant.price
        return self.quantity * self.product.price
    


