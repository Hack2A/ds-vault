import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from Encryption.user_manager import UserManager
from Encryption.vault_core import VaultCore
from Encryption.encryption import FileEncryption, AESGCMEncryption
from Encryption.key_derivation import KeyDerivation


class VaultAPI:
    """
    Stateless API layer over VaultCore.

    Every call is self-contained: username is used to load the correct
    VaultCore (and thus the right blockchain + metadata) on each call.
    """

    def __init__(self, users_dir: str = None):
        if users_dir is None:
            users_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vault_users")
        self.user_manager = UserManager(users_dir)
        self._cores: dict[str, VaultCore] = {}


    def _get_core(self, username: str) -> VaultCore | None:
        """Return a cached VaultCore for the user, or None if user doesn't exist."""
        if username not in self.user_manager.list_users():
            return None
        if username not in self._cores:
            vault_dir = self.user_manager.get_user_vault_dir(username)
            self._cores[username] = VaultCore(username, vault_dir)
        return self._cores[username]

    def _fail(self, error: str) -> dict:
        return {"success": False, "error": error}

    def encrypt(
        self,
        username: str,
        item_name: str,
        plaintext: str,
        advanced: bool,
        seed_phrase: str = "",
    ) -> dict:
        
        core = self._get_core(username)
        if core is None:
            return self._fail(f"User '{username}' not found")

        data_bytes = plaintext.encode("utf-8")
        original_hash = FileEncryption.compute_file_hash(data_bytes)

        if not advanced:
            # Normal mode — random key, no blockchain
            key = os.urandom(32)
            encrypted_data, nonce = AESGCMEncryption.encrypt_data(data_bytes, key)

            core.metadata[item_name] = {
                "original_hash": original_hash,
                "nonce": nonce.hex(),
                "raw_key": key.hex(),
                "salt": None,
                "file_size": len(data_bytes),
                "encrypted_size": len(encrypted_data),
                "is_text": True,
                "mode": "normal",
                "block_number": None,
            }
            core._save_metadata()

            return {
                "success": True,
                "ciphertext": encrypted_data.hex(),
                "item_name": item_name,
            }

        else:
            # Advanced mode — Argon2 key from seed phrase + blockchain record
            salt = os.urandom(16)
            key = KeyDerivation.derive_master_key(seed_phrase, salt)
            encrypted_data, nonce = AESGCMEncryption.encrypt_data(data_bytes, key)

            block_data = {
                "type": "vault_record",
                "item_name": item_name,
                "original_hash": original_hash,
                "salt": salt.hex(),
                "nonce": nonce.hex(),
            }
            block = core.blockchain.add_block(block_data)

            core.metadata[item_name] = {
                "original_hash": original_hash,
                "salt": salt.hex(),
                "nonce": nonce.hex(),
                "raw_key": None,
                "file_size": len(data_bytes),
                "encrypted_size": len(encrypted_data),
                "is_text": True,
                "mode": "advanced",
                "block_number": block.index,
                "block_hash": block.hash,
            }
            core._save_metadata()

            return {
                "success": True,
                "ciphertext": encrypted_data.hex(),
                "block_hash": block.hash,
                "item_name": item_name,
            }

    def decrypt(
        self,
        username: str,
        item_name: str,
        ciphertext_hex: str,
        advanced: bool,
        seed_phrase: str = "",
        block_hash: str = "",
    ) -> dict:
        """
        Decrypt a previously encrypted item.

        Normal mode  (advanced=False):
            - Reads raw_key from metadata, decrypts directly.
            - Returns: { success, plaintext }

        Advanced mode (advanced=True):
            - seed_phrase verified first.
            - Block found by block_hash; salt + nonce read from block data.
            - Returns: { success, plaintext }
        """
        core = self._get_core(username)
        if core is None:
            return self._fail(f"User '{username}' not found")

        if item_name not in core.metadata:
            return self._fail(f"Item '{item_name}' not found in vault")

        meta = core.metadata[item_name]

        try:
            encrypted_data = bytes.fromhex(ciphertext_hex)
        except ValueError:
            return self._fail("Invalid ciphertext — not valid hex")

        if not advanced:
            # Normal mode — key is in metadata
            raw_key = meta.get("raw_key")
            if not raw_key:
                return self._fail("No raw key found for this item (was it stored in normal mode?)")

            nonce = bytes.fromhex(meta["nonce"])
            key = bytes.fromhex(raw_key)
            valid, plaintext_bytes = AESGCMEncryption.decrypt_data(encrypted_data, key, nonce)

            if not valid:
                return self._fail("Decryption failed — data may be corrupted")

        else:
            # Advanced mode — find block, re-derive key from seed phrase
            if not block_hash:
                return self._fail("block_hash is required for advanced mode decrypt")

            block = core.find_block_by_hash(block_hash)
            if block is None:
                return self._fail(f"Block '{block_hash[:16]}...' not found on blockchain")

            block_data = block.data
            if not isinstance(block_data, dict) or block_data.get("item_name") != item_name:
                return self._fail("Block found but does not match the requested item")

            salt = bytes.fromhex(block_data["salt"])
            nonce = bytes.fromhex(block_data["nonce"])
            key = KeyDerivation.derive_master_key(seed_phrase, salt)
            valid, plaintext_bytes = AESGCMEncryption.decrypt_data(encrypted_data, key, nonce)

            if not valid:
                return self._fail("Decryption failed — wrong seed phrase or corrupted data")

            # Final hash integrity check against block record
            current_hash = FileEncryption.compute_file_hash(plaintext_bytes)
            if current_hash != block_data["original_hash"]:
                return self._fail("Integrity check failed — content may have been tampered")

        try:
            plaintext = plaintext_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return self._fail("Decrypted data is not valid UTF-8 text")

        return {"success": True, "plaintext": plaintext}
