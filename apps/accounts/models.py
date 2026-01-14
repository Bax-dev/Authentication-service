from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import TimeStampedModel


class User(AbstractUser, TimeStampedModel):
    username = None
    email = models.EmailField(unique=True, verbose_name='email address')
    is_email_verified = models.BooleanField(default=False, verbose_name='email verified')
    otp_secret = models.CharField(max_length=32, blank=True, null=True, verbose_name='OTP secret')
    otp_created_at = models.DateTimeField(blank=True, null=True, verbose_name='OTP creation time')
    otp_backup_codes = models.JSONField(default=list, blank=True, verbose_name='OTP backup codes')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def get_short_name(self):
        return self.first_name or self.email
