import sys
import os

# Add project root to path so Encryption module is importable
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import hashlib
from Encryption.vault_api import VaultAPI

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserProfile
from .models import NormalVaultItem, AdvancedVaultItem
from .serializers import StoreItemSerializer

# Module-level VaultAPI instance (stateless, cache-backed)
_vault_api = VaultAPI()


def _hash_seed_phrase(seed_phrase: str) -> str:
    """SHA-256 hash of the seed phrase — identical to SeedPhraseAuth._phrase_to_hash."""
    return hashlib.sha256(seed_phrase.strip().encode("utf-8")).hexdigest()


class StoreItemView(APIView):
    """
    POST /api/vault/store/
    Body: { name, body, is_adv, seed_phrase? }
    Requires: Authorization: Bearer <access_token>

    Normal mode  (is_adv=false): AES-GCM with random key → stored in vault_normalvaultitem table.
    Advanced mode (is_adv=true): verifies seed_phrase, Argon2 key + blockchain → stored in vault_advancedvaultitem table.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = StoreItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        name = serializer.validated_data['name']
        body = serializer.validated_data['body']
        is_adv = serializer.validated_data['is_adv']
        seed_phrase = serializer.validated_data.get('seed_phrase', '').strip()

        # Check for duplicate item name for this user in the relevant table
        if is_adv:
            if AdvancedVaultItem.objects.filter(user=user, name=name).exists():
                return Response(
                    {"detail": f"An advanced item named '{name}' already exists in your vault."},
                    status=status.HTTP_409_CONFLICT,
                )
        else:
            if NormalVaultItem.objects.filter(user=user, name=name).exists():
                return Response(
                    {"detail": f"A normal item named '{name}' already exists in your vault."},
                    status=status.HTTP_409_CONFLICT,
                )

        if is_adv:
            # Verify seed phrase against stored hash
            try:
                profile = user.profile
            except UserProfile.DoesNotExist:
                return Response(
                    {"detail": "User profile not found. Please contact support."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            if not profile.seed_phrase_hash:
                return Response(
                    {"detail": "No seed phrase found for your account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            provided_hash = _hash_seed_phrase(seed_phrase)
            if provided_hash != profile.seed_phrase_hash:
                return Response(
                    {"detail": "Incorrect seed phrase. Advanced encryption denied."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Auto-provision the VaultCore user if this is their first vault operation.
        # VaultAPI uses its own file-based UserManager separate from Django's DB.
        if user.username not in _vault_api.user_manager.list_users():
            _vault_api.user_manager.register_user(user.username)

        # Encrypt via VaultAPI
        result = _vault_api.encrypt(
            username=user.username,
            item_name=name,
            plaintext=body,
            advanced=is_adv,
            seed_phrase=seed_phrase,
        )

        if not result.get("success"):
            return Response(
                {"detail": result.get("error", "Encryption failed.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if is_adv:
            vault_item = AdvancedVaultItem.objects.create(
                user=user,
                name=name,
                ciphertext=result["ciphertext"],
                block_hash=result["block_hash"],
            )
            return Response(
                {
                    "message": "Item encrypted and stored (advanced mode).",
                    "item_name": vault_item.name,
                    "is_advanced": True,
                    "ciphertext": vault_item.ciphertext,
                    "block_hash": vault_item.block_hash,
                    "created_at": vault_item.created_at,
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            vault_item = NormalVaultItem.objects.create(
                user=user,
                name=name,
                ciphertext=result["ciphertext"],
            )
            return Response(
                {
                    "message": "Item encrypted and stored (normal mode).",
                    "item_name": vault_item.name,
                    "is_advanced": False,
                    "ciphertext": vault_item.ciphertext,
                    "created_at": vault_item.created_at,
                },
                status=status.HTTP_201_CREATED,
            )
