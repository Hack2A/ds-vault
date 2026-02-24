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
            "file_uuid": file_uuid
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
        if file_uuid in self.metadata:
            del self.metadata[file_uuid]
    
    def get_all_metadata(self) -> dict:
        return dict(self.metadata)
    
    def encrypt_metadata(self) -> tuple:
        plaintext = json.dumps(self.metadata).encode('utf-8')
        ciphertext, nonce = AESGCMEncryption.encrypt_data(
            plaintext,
            self.metadata_key,
            associated_data=b"metadata_v2"
        )
        return ciphertext, nonce
    
    def decrypt_metadata(self, ciphertext: bytes, nonce: bytes) -> bool:
        success, plaintext = AESGCMEncryption.decrypt_data(
            ciphertext,
            self.metadata_key,
            nonce,
            associated_data=b"metadata_v2"
        )
        
        if not success:
            return False
        
        try:
            self.metadata = json.loads(plaintext.decode('utf-8'))
            return True
        except Exception:
            return False


class VaultStorage:
    
    def __init__(self, vault_path: str):
        self.vault_path = vault_path
        os.makedirs(vault_path, exist_ok=True)
    
    def get_vault_file_path(self, file_uuid: str) -> str:
        return os.path.join(self.vault_path, f"{file_uuid}.enc")
    
    def get_metadata_path(self) -> str:
        return os.path.join(self.vault_path, "metadata.enc")
    
    def get_merkle_path(self) -> str:
        return os.path.join(self.vault_path, "merkle_state.enc")
    
    def get_signature_path(self) -> str:
        return os.path.join(self.vault_path, "root_signature.bin")
    
    def get_keyinfo_path(self) -> str:
        return os.path.join(self.vault_path, "keyinfo.json")
    
    def save_encrypted_file(self, file_uuid: str, ciphertext: bytes):
        file_path = self.get_vault_file_path(file_uuid)
        with open(file_path, 'wb') as f:
            f.write(ciphertext)
    
    def load_encrypted_file(self, file_uuid: str) -> bytes:
        file_path = self.get_vault_file_path(file_uuid)
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return f.read()
        return None
    
    def file_exists(self, file_uuid: str) -> bool:
        return os.path.exists(self.get_vault_file_path(file_uuid))
    
    def delete_file(self, file_uuid: str):
        file_path = self.get_vault_file_path(file_uuid)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    def save_metadata(self, ciphertext: bytes, nonce: bytes):
        metadata_path = self.get_metadata_path()
        data = {
            "ciphertext": ciphertext.hex(),
            "nonce": nonce.hex()
        }
        with open(metadata_path, 'w') as f:
            json.dump(data, f)
    
    def load_metadata(self) -> tuple:
        metadata_path = self.get_metadata_path()
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                data = json.load(f)
            ciphertext = bytes.fromhex(data["ciphertext"])
            nonce = bytes.fromhex(data["nonce"])
            return ciphertext, nonce
        return None, None
    
    def save_merkle_state(self, ciphertext: bytes, nonce: bytes):
        merkle_path = self.get_merkle_path()
        data = {
            "ciphertext": ciphertext.hex(),
            "nonce": nonce.hex()
        }
        with open(merkle_path, 'w') as f:
            json.dump(data, f)
    
    def load_merkle_state(self) -> tuple:
        merkle_path = self.get_merkle_path()
        if os.path.exists(merkle_path):
            with open(merkle_path, 'r') as f:
                data = json.load(f)
            ciphertext = bytes.fromhex(data["ciphertext"])
            nonce = bytes.fromhex(data["nonce"])
            return ciphertext, nonce
        return None, None
    
    def save_signature(self, signature: bytes):
        sig_path = self.get_signature_path()
        with open(sig_path, 'wb') as f:
            f.write(signature)
    
    def load_signature(self) -> bytes:
        sig_path = self.get_signature_path()
        if os.path.exists(sig_path):
            with open(sig_path, 'rb') as f:
                return f.read()
        return None
    
    def save_keyinfo(self, key_info: dict):
        keyinfo_path = self.get_keyinfo_path()
        with open(keyinfo_path, 'w') as f:
            json.dump(key_info, f)
    
    def load_keyinfo(self) -> dict:
        keyinfo_path = self.get_keyinfo_path()
        if os.path.exists(keyinfo_path):
            with open(keyinfo_path, 'r') as f:
                return json.load(f)
        return None
    
    def list_vault_files(self) -> list:
        files = []
        for fname in os.listdir(self.vault_path):
            if fname.endswith(".enc"):
                file_uuid = fname[:-4]
                files.append(file_uuid)
        return files
