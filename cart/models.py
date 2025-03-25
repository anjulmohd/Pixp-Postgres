from django.db import models
from django.contrib.auth import get_user_model
from myapp.models import Product,ProductVariant

User = get_user_model()

# Create your models here.
class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    code = models.CharField(max_length=20, unique=True, help_text="Unique coupon code")
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=10,default="10", decimal_places=2, help_text="Discount amount or percentage")
    expiration_date = models.DateTimeField(help_text="Expiration date of the coupon")
    usage_limit = models.PositiveIntegerField(default=1, help_text="Maximum times the coupon can be used")
    used_count = models.PositiveIntegerField(default=0, help_text="Number of times the coupon has been used")
    is_active = models.BooleanField(default=True, help_text="Whether the coupon is active or not")

    

    def is_valid(self):
        """Check if the coupon is still valid based on expiration date and usage limit."""
        from django.utils.timezone import now
        return self.is_active and self.expiration_date > now() and self.used_count < self.usage_limit
    

    

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Add this
    updated_at = models.DateTimeField(auto_now=True)  # Add this

class Cart_items(models.Model):
    cart = models.ForeignKey(Cart, related_name='cart_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.CASCADE)  # Can be null if variant is selected
    product_variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.CASCADE)  # Can be null if base product is selected
    quantity = models.PositiveIntegerField(default=1)

    def save(self, *args, **kwargs):
        # Ensure only one of product or product_variant is set
        if self.product and self.product_variant:
            raise ValueError("Cannot have both product and product_variant set at the same time.")
        if not self.product and not self.product_variant:
            raise ValueError("Either product or product_variant must be set.")
        super().save(*args, **kwargs)

    def __str__(self):
        if self.product_variant:
            return f"{self.product_variant.name} - {self.cart.user.username}"
        return f"{self.product.name} - {self.cart.user.username}"

    def get_total_price(self):
    # If a product_variant is selected, calculate the price using the variant
        if self.product_variant:
            return self.quantity * self.product_variant.price
        # If no variant is selected, calculate the price using the base product
        return self.quantity * self.product.price



class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Wishlist for {self.user.username}"

class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='wishlist_items', on_delete=models.CASCADE ,null=True, blank=True)
    product_variant = models.ForeignKey(ProductVariant, null=True, blank=True, related_name='wishlist_variant_items', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('wishlist', 'product', 'product_variant')

    def save(self, *args, **kwargs):
        # Ensure only one of product or product_variant is set
        if self.product and self.product_variant:
            raise ValueError("Cannot have both product and product_variant set at the same time.")
        if not self.product and not self.product_variant:
            raise ValueError("Either product or product_variant must be set.")
        super().save(*args, **kwargs)

    def __str__(self):
        if self.product_variant:
            return f"Item: {self.product_variant.name} in wishlist {self.wishlist.id}"
        return f"Item: {self.product.name} in wishlist {self.wishlist.id}"