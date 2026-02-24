from django.urls import path
from .views import StoreItemView

urlpatterns = [
    path('store/', StoreItemView.as_view(), name='vault-store'),
]
