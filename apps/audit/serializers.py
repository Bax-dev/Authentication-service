
from rest_framework import serializers
from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = AuditLog
        fields = [
            'id', 'event', 'email', 'ip_address', 'user_agent',
            'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'event', 'email', 'ip_address',
                          'user_agent', 'metadata', 'created_at']


class AuditLogDetailSerializer(AuditLogSerializer):
    formatted_metadata = serializers.SerializerMethodField()

    class Meta(AuditLogSerializer.Meta):
        fields = AuditLogSerializer.Meta.fields + ['formatted_metadata']

    def get_formatted_metadata(self, obj):
        if not obj.metadata:
            return {}

        formatted = dict(obj.metadata)

        if 'timestamp' in formatted:
            formatted['timestamp_readable'] = formatted['timestamp']

        return formatted
