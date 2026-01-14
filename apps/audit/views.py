
import django_filters
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics, permissions
from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer, AuditLogDetailSerializer
from apps.core.filters import BaseFilterSet, OrderingFilter
from apps.core.pagination import StandardResultsSetPagination


class AuditLogFilter(BaseFilterSet):

    email = django_filters.CharFilter(field_name='email', lookup_expr='icontains')
    event = django_filters.CharFilter(field_name='event', lookup_expr='icontains')
    ip_address = django_filters.CharFilter(field_name='ip_address', lookup_expr='icontains')

    from_datetime = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    to_datetime = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    event_type = django_filters.CharFilter(method='filter_event_type')

    metadata_key = django_filters.CharFilter(method='filter_metadata_key')
    metadata_value = django_filters.CharFilter(method='filter_metadata_value')

    # Ordering
    ordering = OrderingFilter(
        fields=[
            ('created_at', 'created_at'),
            ('-created_at', '-created_at'),
            ('event', 'event'),
            ('email', 'email'),
            ('ip_address', 'ip_address'),
        ]
    )

    class Meta:
        model = AuditLog
        fields = [
            'email', 'event', 'ip_address', 'from_datetime', 'to_datetime',
            'event_type', 'metadata_key', 'metadata_value'
        ]

    def filter_metadata_key(self, queryset, name, value):
        return queryset.filter(metadata__has_key=value)

    def filter_metadata_value(self, queryset, name, value):
        return queryset.filter(metadata__icontains=value)

    def filter_event_type(self, queryset, name, value):
        value = value.lower()

        if value == 'auth':
            return queryset.filter(
                Q(event__icontains='login') |
                Q(event__icontains='logout') |
                Q(event__icontains='token') |
                Q(event__icontains='otp') |
                Q(event__icontains='password')
            )
        elif value == 'user':
            return queryset.filter(
                Q(event__icontains='user') |
                Q(event__icontains='profile') |
                Q(event__icontains='register') |
                Q(event__icontains='account')
            )
        elif value == 'security':
            return queryset.filter(
                Q(event__icontains='lock') |
                Q(event__icontains='unlock') |
                Q(event__icontains='failed') |
                Q(event__icontains='suspicious')
            )
        elif value == 'admin':
            return queryset.filter(
                Q(event__icontains='admin') |
                Q(event__icontains='staff') |
                Q(event__icontains='permission')
            )
        elif value == 'system':
            return queryset.filter(
                Q(event__icontains='system') |
                Q(event__icontains='cleanup') |
                Q(event__icontains='maintenance')
            )

        return queryset


@extend_schema(
    summary="List Audit Logs",
    description="Retrieve paginated audit logs with comprehensive filtering. Requires JWT authentication. Non-admin users can only see their own logs.",
    parameters=[
        OpenApiParameter(
            name='email',
            type=str,
            description='Filter by email address (partial match)',
            required=False
        ),
        OpenApiParameter(
            name='event',
            type=str,
            description='Filter by event name (partial match)',
            required=False
        ),
        OpenApiParameter(
            name='ip_address',
            type=str,
            description='Filter by IP address (partial match)',
            required=False
        ),
        OpenApiParameter(
            name='from_datetime',
            type={'type': 'string', 'format': 'date-time'},
            description='Filter logs from this datetime onwards (ISO format)',
            required=False
        ),
        OpenApiParameter(
            name='to_datetime',
            type={'type': 'string', 'format': 'date-time'},
            description='Filter logs up to this datetime (ISO format)',
            required=False
        ),
        OpenApiParameter(
            name='event_type',
            type=str,
            description='Filter by event category: auth, user, security, admin, system',
            required=False,
            enum=['auth', 'user', 'security', 'admin', 'system']
        ),
        OpenApiParameter(
            name='metadata_key',
            type=str,
            description='Filter by metadata key existence',
            required=False
        ),
        OpenApiParameter(
            name='metadata_value',
            type=str,
            description='Filter by metadata value content (partial match)',
            required=False
        ),
        OpenApiParameter(
            name='ordering',
            type=str,
            description='Order by: created_at, -created_at, event, email, ip_address',
            required=False
        ),
    ],
    responses={
        200: AuditLogSerializer(many=True),
        401: "Unauthorized - JWT token required"
    }
)
class AuditLogListView(generics.ListAPIView):

    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = AuditLogFilter
    pagination_class = StandardResultsSetPagination
    ordering = ['-created_at']

    def get_queryset(self):

        queryset = super().get_queryset()

        if not self.request.user.is_staff:
            queryset = queryset.filter(email=self.request.user.email)

        return queryset


@extend_schema(
    summary="Get Audit Log Detail",
    description="Retrieve detailed information about a specific audit log entry. Requires JWT authentication. Non-admin users can only access their own logs.",
    responses={
        200: AuditLogDetailSerializer,
        401: "Unauthorized - JWT token required",
        404: "Audit log not found"
    }
)
class AuditLogDetailView(generics.RetrieveAPIView):

    queryset = AuditLog.objects.all()
    serializer_class = AuditLogDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        if not self.request.user.is_staff:
            queryset = queryset.filter(email=self.request.user.email)

        return queryset
