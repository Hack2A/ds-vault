import logging
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from Encryption.user_manager import UserManager
from Encryption.vault_core import VaultCore
from Encryption.encryption import FileEncryption, AESGCMEncryption
from Encryption.key_derivation import KeyDerivation

logger = logging.getLogger(__name__)

# ─── Web3 / IPFS (loaded lazily; flags control whether they are used) ─────────
# Importing here would fail if web3 package is not installed, so we defer.

def _get_blockchain_flags() -> tuple[bool, bool]:
    """Return (USE_BLOCKCHAIN, USE_IPFS) feature flags.

    Imports web3.config lazily so the vault works normally even when the web3
    package is not installed or not on sys.path.

    Returns
    -------
    (bool, bool)
        (USE_BLOCKCHAIN, USE_IPFS) — both False on any import error.
    """
    try:
        from web3_addon.config import USE_BLOCKCHAIN, USE_IPFS
        return USE_BLOCKCHAIN, USE_IPFS
    except Exception:
        return False, False


def _store_on_chain(file_hash_hex: str, cid: str) -> str:
    """Submit hash + CID to the blockchain smart contract.

    Parameters
    ----------
    file_hash_hex : str
        SHA-256 hex digest of the plaintext.
    cid : str
        IPFS Content Identifier, or empty string.

    Returns
    -------
    str
        Transaction hash on success, empty string on any failure.
    """
    try:
        from web3_addon.contract_client import store_record
        tx_hash = store_record(file_hash_hex, cid)
        return tx_hash or ""
    except Exception as exc:
        logger.warning("_store_on_chain failed (local vault unaffected): %s", exc)
        return ""


def _upload_to_ipfs(data: bytes, item_name: str) -> str:
    """Pin encrypted bytes to IPFS via Pinata.

    Parameters
    ----------
    data : bytes
        Encrypted ciphertext bytes.
    item_name : str
        Logical filename for the Pinata dashboard.

    Returns
    -------
    str
        IPFS CID on success, empty string on any failure.
    """
    try:
        from web3_addon.ipfs_client import upload_to_ipfs
        cid = upload_to_ipfs(data, filename=f"{item_name}.enc")
        return cid or ""
    except Exception as exc:
        logger.warning("_upload_to_ipfs failed (vault continues): %s", exc)
        return ""


def _verify_on_chain(file_hash_hex: str, item_name: str) -> None:
    """Cross-check decrypted hash against the on-chain record.

    Raises
    ------
    ValueError
        If an on-chain record exists AND its stored hash does NOT match the
        freshly computed hash — indicating tampering.

    Note: if no on-chain record exists (legacy data pre-dating Web3 integration),
    the check is silently skipped to preserve backward compatibility.
    """
    try:
        from web3_addon.contract_client import get_record
        on_chain = get_record(file_hash_hex)
        if on_chain is None:
            # No record found — legacy item or blockchain was disabled during encrypt.
            logger.info(
                "No on-chain record for '%s' — skipping chain verification (backward compat).",
                item_name,
            )
            return
        stored_hash = on_chain.get("file_hash", "")
        if stored_hash and stored_hash != file_hash_hex:
            raise ValueError(
                f"Chain verification FAILED for '{item_name}': "
                f"on-chain hash '{stored_hash[:16]}...' "
                f"does not match computed hash '{file_hash_hex[:16]}...'. "
                "Content may have been tampered with."
            )
        logger.info("Chain verification PASSED for '%s'.", item_name)
    except ValueError:
        raise  # Re-raise tampering errors — these must reach the caller
    except Exception as exc:
        logger.warning(
            "_verify_on_chain check failed (non-blocking, decryption continues): %s", exc
        )


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
            # Advanced mode — Argon2 key from seed phrase + local blockchain record
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
            block = core.blockchain.add_block(block_data)  # local PoW chain — unchanged

            # ── Web3 add-on (advanced mode only) ──────────────────────────────
            # These calls are optional and non-blocking.
            # Failures fall back to empty strings; local vault is never affected.
            use_bc, use_ipfs = _get_blockchain_flags()

            cid = ""
            if use_ipfs:
                cid = _upload_to_ipfs(encrypted_data, item_name)

            tx_hash = ""
            if use_bc:
                tx_hash = _store_on_chain(original_hash, cid)
            # ── End Web3 add-on ───────────────────────────────────────────────

            core.metadata[item_name] = {
                # ── existing fields (unchanged) ──────────────────────────────
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
                # ── new Web3 fields (safe defaults; backward compatible) ──────
                "tx_hash": tx_hash,
                "cid": cid,
                "chain_verified": bool(tx_hash),
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

            # Final hash integrity check against local block record (unchanged)
            current_hash = FileEncryption.compute_file_hash(plaintext_bytes)
            if current_hash != block_data["original_hash"]:
                return self._fail("Integrity check failed — content may have been tampered")

            # ── Web3 chain verification add-on ────────────────────────────────
            # Only runs when USE_BLOCKCHAIN=True AND the item has a tx_hash
            # (i.e., was encrypted after Web3 was enabled).
            # Legacy items with no tx_hash are silently skipped.
            use_bc, _ = _get_blockchain_flags()
            if use_bc and meta.get("tx_hash"):
                try:
                    _verify_on_chain(current_hash, item_name)
                except ValueError as tamper_err:
                    return self._fail(str(tamper_err))
            # ── End Web3 add-on ───────────────────────────────────────────────

        try:
            plaintext = plaintext_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return self._fail("Decrypted data is not valid UTF-8 text")

        return {"success": True, "plaintext": plaintext}
