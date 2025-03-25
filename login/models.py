from django.db import models
import random
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.timezone import now, timedelta
from datetime import timedelta
from django.utils import timezone
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import string



# Create your models here.
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    is_blocked = models.BooleanField(default=False)  # Field to block users

    groups = models.ManyToManyField(Group, related_name="customuser_set", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="customuser_permissions_set", blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', max_length=255, null=True, blank=True)

    
    
    
    def save(self, *args, **kwargs):
        """Resize the image to a square before saving and convert RGBA to RGB."""
        
        if self.pk:  # Ensure the user exists before modifying images
            existing_user = CustomUser.objects.filter(pk=self.pk).first()
            if existing_user and existing_user.profile_picture == self.profile_picture:
                # If the image hasn't changed, don't process it again
                super().save(*args, **kwargs)
                return

        if self.profile_picture:
            img = Image.open(self.profile_picture)

            # Convert RGBA or P mode images to RGB
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            min_size = min(img.size)
            img = img.resize((min_size, min_size))  # Resize to square

            # Save the resized image
            img_io = BytesIO()
            img.save(img_io, format='JPEG', quality=90)
            self.profile_picture.save(self.profile_picture.name, ContentFile(img_io.getvalue()), save=False)

        super().save(*args, **kwargs)  # Save only once

    def __str__(self):
        return self.username
    
class OTPVerification(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)  # Store the OTP
    created_at = models.DateTimeField(auto_now_add=True)
    expiry_time = models.DateTimeField(default=now)

    def is_expired(self):
    
      return (timezone.now() - self.created_at) > timedelta(seconds=30)
    
    def __str__(self):
        return f"OTP for {self.user.username}"
    
