from django.db import models
from apps.core.models import TimeStampedModel


class AuditLog(TimeStampedModel):
    event = models.CharField(max_length=255)
    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=500)  
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        return f"{self.event} - {self.email} - {self.created_at}"
