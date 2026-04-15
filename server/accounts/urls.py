from django.urls import re_path
from .views import LoginView, ProfileView, RegisterView, VerifyOTPView

urlpatterns = [
    re_path(r'^register/?$', RegisterView.as_view(), name='auth-register'),
    re_path(r'^login/?$', LoginView.as_view(), name='auth-login'),
    re_path(r'^verify-otp/?$', VerifyOTPView.as_view(), name='auth-verify-otp'),
    re_path(r'^profile/?$', ProfileView.as_view(), name='auth-profile'),
]
