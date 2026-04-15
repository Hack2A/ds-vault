from django.urls import re_path
from .views import StoreItemView, ListVaultItemsView, DecryptItemView

urlpatterns = [
    re_path(r'^store/?$', StoreItemView.as_view(), name='vault-store'),
    re_path(r'^items/?$', ListVaultItemsView.as_view(), name='vault-items'),
    re_path(r'^decrypt/?$', DecryptItemView.as_view(), name='vault-decrypt'),
]
