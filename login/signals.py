from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser
from payment.models import Wallet

@receiver(post_save, sender=CustomUser)
def create_wallet(sender, instance, created, **kwargs):
    """Automatically create a wallet when a new user is created."""
    if created:  # Only for new users
        Wallet.objects.create(user=instance)
