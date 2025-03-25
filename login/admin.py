from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active', 'is_blocked')
    list_filter = ('is_staff', 'is_active', 'is_blocked')
    fieldsets = UserAdmin.fieldsets + ((None, {'fields': ('is_blocked',)}),)

admin.site.register(CustomUser, CustomUserAdmin)

