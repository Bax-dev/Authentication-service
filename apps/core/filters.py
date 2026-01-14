
import django_filters
from django.db import models


class BaseFilterSet(django_filters.FilterSet):
    created_at = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at__lte = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_at = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_at__lte = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')

    class Meta:
        fields = ['created_at', 'updated_at']


class OrderingFilter(django_filters.OrderingFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.extra.get('choices'):
            self.extra['choices'] = [
                ('created_at', 'Oldest First'),
                ('-created_at', 'Newest First'),
                ('updated_at', 'Recently Updated'),
                ('-updated_at', 'Least Recently Updated'),
            ]
