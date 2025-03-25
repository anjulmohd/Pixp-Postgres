from django.contrib import admin
from .models import PaymentOrder,PaymentOrderItem,Wallet,WalletTransaction

# Register your models here.
admin.site.register(PaymentOrder)
admin.site.register(PaymentOrderItem)
admin.site.register(Wallet)
admin.site.register(WalletTransaction)