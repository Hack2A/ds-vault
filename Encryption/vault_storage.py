import json
import os
import uuid
from datetime import datetime
from Encryption.encryption import AESGCMEncryption
from Encryption.crypto_constants import UUID_LENGTH


class EncryptedMetadata:

    def __init__(self, metadata_key: bytes):
        self.metadata_key = metadata_key
        self.metadata = {}

    def add_file(self, filename: str, file_hash: bytes, file_size: int) -> str:
        file_uuid = uuid.uuid4().hex[:UUID_LENGTH]
        self.metadata[file_uuid] = {
            "original_filename": filename,
            "file_hash": file_hash.hex(),
            "file_size": file_size,
            "uploaded_at": datetime.utcnow().isoformat(),
            "file_uuid": file_uuid,
        }
        return file_uuid

    def get_file_info(self, file_uuid: str) -> dict:
        return self.metadata.get(file_uuid)

    def get_file_by_name(self, filename: str) -> str:
        for file_uuid, info in self.metadata.items():
            if info.get("original_filename") == filename:
                return file_uuid
        return None

    def list_files(self) -> list:
        return list(self.metadata.keys())

    def remove_file(self, file_uuid: str):
        self.metadata.pop(file_uuid, None)

    def get_all_metadata(self) -> dict:
        return dict(self.metadata)

    def encrypt_metadata(self) -> tuple:
        plaintext = json.dumps(self.metadata).encode("utf-8")
        return AESGCMEncryption.encrypt_data(
            plaintext, self.metadata_key, associated_data=b"metadata_v2"
        )

    def decrypt_metadata(self, ciphertext: bytes, nonce: bytes) -> bool:
        success, plaintext = AESGCMEncryption.decrypt_data(
            ciphertext, self.metadata_key, nonce, associated_data=b"metadata_v2"
        )
        if not success:
            return False
        try:
            self.metadata = json.loads(plaintext.decode("utf-8"))
            return True
        except Exception:
            return False


class VaultStorage:

    def __init__(self, vault_path: str):
        self.vault_path = vault_path
        os.makedirs(vault_path, exist_ok=True)

    # ── path helpers ────────────────────────────────────────────────────────
    def _path(self, filename: str) -> str:
        return os.path.join(self.vault_path, filename)

    def get_vault_file_path(self, file_uuid: str) -> str:
        return self._path(f"{file_uuid}.enc")

    # ── generic JSON helpers (DRY) ───────────────────────────────────────────
    def _save_json(self, path: str, data: dict):
        with open(path, "w") as f:
            json.dump(data, f)

    def _load_json(self, path: str) -> dict | None:
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)

    def _save_encrypted_blob(self, path: str, ciphertext: bytes, nonce: bytes):
        self._save_json(path, {"ciphertext": ciphertext.hex(), "nonce": nonce.hex()})

    def _load_encrypted_blob(self, path: str) -> tuple:
        data = self._load_json(path)
        if not data:
            return None, None
        return bytes.fromhex(data["ciphertext"]), bytes.fromhex(data["nonce"])

    # ── encrypted file storage ───────────────────────────────────────────────
    def file_exists(self, file_uuid: str) -> bool:
        return os.path.exists(self.get_vault_file_path(file_uuid))

    def delete_file(self, file_uuid: str):
        path = self.get_vault_file_path(file_uuid)
        if os.path.exists(path):
            os.remove(path)

    def list_vault_files(self) -> list:
        return [f[:-4] for f in os.listdir(self.vault_path) if f.endswith(".enc")]

    # ── metadata ─────────────────────────────────────────────────────────────
    def save_metadata(self, ciphertext: bytes, nonce: bytes):
        self._save_encrypted_blob(self._path("metadata.enc"), ciphertext, nonce)

    def load_metadata(self) -> tuple:
        return self._load_encrypted_blob(self._path("metadata.enc"))

    # ── merkle state ─────────────────────────────────────────────────────────
    def save_merkle_state(self, ciphertext: bytes, nonce: bytes):
        self._save_encrypted_blob(self._path("merkle_state.enc"), ciphertext, nonce)

    def load_merkle_state(self) -> tuple:
        return self._load_encrypted_blob(self._path("merkle_state.enc"))

    # ── signature ────────────────────────────────────────────────────────────
    def save_signature(self, signature: bytes):
        with open(self._path("root_signature.bin"), "wb") as f:
            f.write(signature)

    def load_signature(self) -> bytes | None:
        path = self._path("root_signature.bin")
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return f.read()

    # ── key info ─────────────────────────────────────────────────────────────
    def save_keyinfo(self, key_info: dict):
        self._save_json(self._path("keyinfo.json"), key_info)

    def load_keyinfo(self) -> dict | None:
        return self._load_json(self._path("keyinfo.json"))
