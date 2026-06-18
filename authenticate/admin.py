"""Authenticate admin."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from . models import CustomerModel
# Register your models here.


@admin.register(CustomerModel)
class CustomerAdmin(UserAdmin):
    """Admin class for CustomerModel."""

    list_display = (
        "id",
        "email",
        "phone_number",
        "is_staff",
        "is_active"
        )
    ordering = ["id"]
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('phone_number',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'phone_number'),
        }),
    )
