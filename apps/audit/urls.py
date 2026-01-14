
from django.urls import path
from apps.audit import views

app_name = 'audit'

urlpatterns = [
    path('logs/', views.AuditLogListView.as_view(), name='audit-log-list'),
    path('logs/<int:pk>/', views.AuditLogDetailView.as_view(), name='audit-log-detail'),
]
