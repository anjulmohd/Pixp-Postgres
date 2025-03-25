from django.db import models
from django.contrib.auth import get_user_model
from myapp.models import Product
import random
import string
User = get_user_model()
import hashlib

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15, null=True, blank=True)  # Optional phone number
    street_address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, null=True, blank=True)  # Optional state
    postal_code = models.CharField(max_length=10, null=True, blank=True)  # Optional postal code
    country = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} - {self.street_address}, {self.city}, {self.country}"

    class Meta:
        ordering = ['-is_default']  # Default address appears first
    def save(self, *args, **kwargs):
        # Check if the address is marked as default
        if self.is_default:
            # Set other addresses as non-default for this user
            Address.objects.filter(user=self.user, is_default=True).exclude(id=self.id).update(is_default=False)

        super(Address, self).save(*args, **kwargs)



    
class ReferralCode(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Referrer (B)
    referrer_code = models.CharField(max_length=20, unique=True)  # Referral code
    referral_count = models.IntegerField(default=0)  # Number of successful referrals

    def __str__(self):
        return f"{self.user.username} - {self.referrer_code} - {self.referral_count} referrals"

    def generate_referral_code(self):
        """Generate a unique referral code based on user ID."""
        random_str = str(random.randint(1000, 9999))
        hash_input = f"{self.user.id}-{random_str}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:10]  # 10-character code


class UsedReferral(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # User who used the referral (A or C)
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="referrals")  # Original referrer (B)
    applied_at = models.DateTimeField(auto_now_add=True)  # Date when referral was applied

    def __str__(self):
        return f"{self.user.username} used {self.referrer.username}'s referral"