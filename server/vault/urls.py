from django.urls import path
from .views import StoreItemView, ListVaultItemsView, DecryptItemView

urlpatterns = [
    path('store/', StoreItemView.as_view(), name='vault-store'),
    path('items/', ListVaultItemsView.as_view(), name='vault-items'),
    path('decrypt/', DecryptItemView.as_view(), name='vault-decrypt'),
]
