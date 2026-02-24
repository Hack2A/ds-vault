from django.db import models
from django.contrib.auth.models import User


class NormalVaultItem(models.Model):
    """
    Normal mode: AES-GCM with a random key stored in VaultCore metadata.
    No seed phrase required.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='normal_vault_items')
    name = models.CharField(max_length=255)
    ciphertext = models.TextField()           # hex-encoded AES-GCM ciphertext
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'name')
        ordering = ['-created_at']

    def __str__(self):
        return f"NormalVaultItem({self.user.username}/{self.name})"


class AdvancedVaultItem(models.Model):
    """
    Advanced mode: AES-GCM with Argon2-derived key from seed phrase + blockchain record.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='advanced_vault_items')
    name = models.CharField(max_length=255)
    ciphertext = models.TextField()           # hex-encoded AES-GCM ciphertext
    block_hash = models.CharField(max_length=64)  # blockchain integrity hash
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'name')
        ordering = ['-created_at']

    def __str__(self):
        return f"AdvancedVaultItem({self.user.username}/{self.name})"
