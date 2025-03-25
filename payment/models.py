from django.db import models
from django.db.models.fields import CharField
from django.utils.translation import gettext_lazy as _
from .constants import PaymentStatus
from django.contrib.auth import get_user_model
from myapp.models import Product,ProductVariant
import random
import string
User = get_user_model()




class PaymentOrder(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("FAILED", "Failed"),
        ("PROCESSED", "Processed"),
        ("SHIPPED", "Shipped"),
        ("DELIVERED", "Delivered"),
        ("RETURN_REQUESTED", "Return Requested"),
        ("RETURN_APPROVED", "Return Approved"),
        ("CANCEL_REQUESTED", "Cancel Requested"),
        ("CANCEL_APPROVED", "Cancel Approved"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order_unique_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    reason = models.TextField(blank=True, null=True)  # New field
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    def save(self, *args, **kwargs):
        if not self.order_unique_id:
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            self.order_unique_id = f"ORD{(self.id or 1000) * 7}{random_part}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"


    
class PaymentOrderItem(models.Model):
    order = models.ForeignKey(PaymentOrder, related_name='order_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE,null=True,blank=True)
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

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def deposit(self, amount, description="Wallet Deposit"):
        """Add money to the wallet and record the transaction."""
        self.balance += amount
        self.save()
        WalletTransaction.objects.create(wallet=self, amount=amount, transaction_type="CREDIT", description=description)

    def deposit_refund(self, amount, order):
        """Deposit a refund with a specific order reference."""
        self.balance += amount
        self.save()
        WalletTransaction.objects.create(
            wallet=self,
            order=order,  # Link the order
            amount=amount,
            transaction_type="REFUND",
            description=f"Refund for Order #{order.order_unique_id}"
            )

    def withdraw(self, amount, description="Wallet Withdrawal"):
        """Withdraw money if sufficient balance is available and record the transaction."""
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            WalletTransaction.objects.create(wallet=self, amount=amount, transaction_type="DEBIT", description=description)
            return True
        return False  # Insufficient balance

    def __str__(self):
        return f"{self.user.username}'s Wallet - Balance: ₹{self.balance}"


class WalletTransaction(models.Model):
    TRANSACTION_TYPES = [
        ("CREDIT", "Credit"),
        ("DEBIT", "Debit"),
        ('REFUND','Refund')
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey("PaymentOrder", on_delete=models.SET_NULL, null=True, blank=True, related_name="refund_transactions")  # Store the order for refunds
    transaction_unique_id = models.CharField(max_length=20, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.transaction_unique_id:
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            self.transaction_unique_id = f"TXN{(self.id or 1000) * 5}{random_part}"
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.wallet.user.username} - {self.transaction_type} - ₹{self.amount}"