from django.urls import path
from .views import StoreItemView, ListVaultItemsView

urlpatterns = [
    path('store/', StoreItemView.as_view(), name='vault-store'),
    path('items/', ListVaultItemsView.as_view(), name='vault-items'),
]
