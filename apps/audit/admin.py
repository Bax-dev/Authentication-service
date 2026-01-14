from django.contrib import admin
from django_json_widget.widgets import JSONEditorWidget
from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):

    list_display = ('event', 'email', 'ip_address', 'created_at')
    list_filter = ('event', 'created_at', 'email')
    search_fields = ('event', 'email', 'ip_address', 'user_agent')
    readonly_fields = ('id', 'event', 'email', 'ip_address', 'user_agent', 'metadata', 'created_at')
    ordering = ('-created_at',)


    formfield_overrides = {
        AuditLog._meta.get_field('metadata').__class__: {
            'widget': JSONEditorWidget
        }
    }

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
