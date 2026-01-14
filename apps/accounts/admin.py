from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.accounts.models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    
    model = User
    list_display = ('email', 'first_name', 'last_name', 'is_email_verified', 'is_active', 'date_joined')
    list_filter = ('is_email_verified', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('is_email_verified', 'otp_secret', 'otp_created_at', 'otp_backup_codes')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_email_verified'),
        }),
    )

    readonly_fields = ('otp_created_at', 'date_joined', 'last_login')
