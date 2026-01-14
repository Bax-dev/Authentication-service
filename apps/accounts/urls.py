
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.accounts import views

app_name = 'auth'

urlpatterns = [
    
    path('otp/request/', views.otp_request, name='otp_request'),
    path('otp/verify/', views.otp_verify, name='otp_verify'),

    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('login/', views.login, name='login'),
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
