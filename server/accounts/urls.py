from django.urls import path
from .views import LoginView, ProfileView, RegisterView, VerifyOTPView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('verify-otp/', VerifyOTPView.as_view(), name='auth-verify-otp'),
    path('profile/', ProfileView.as_view(), name='auth-profile'),
]
