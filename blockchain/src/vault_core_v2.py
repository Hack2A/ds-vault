import os
import json
from hashlib import sha256
from src.key_derivation import KeyDerivation
from src.encryption import AESGCMEncryption
from src.signing import DigitalSignature
from src.merkle_tree import MerkleTree
from src.vault_storage import VaultStorage, EncryptedMetadata
from src.security import RateLimiter, TamperingDetection, SecureMemory


class VaultCoreV2:
    
    def __init__(self, username: str, vault_path: str):
        self.username = username
        self.vault_path = vault_path
        self.storage = VaultStorage(vault_path)
        
        self.encryption_key = None
        self.metadata_key = None
        self.signing_key = None
        self.public_key = None
        
        self.metadata = None
        self.merkle_tree = None
        self.private_key_obj = None
        self.public_key_obj = None
    
    def initialize_vault(self, password: str, salt: bytes = None) -> bool:
        if salt is None:
            salt = KeyDerivation.generate_salt()
        
        master_key = KeyDerivation.derive_master_key(password, salt)
        keys = KeyDerivation.derive_keys(master_key)
        
        self.encryption_key = keys["encryption"]
        self.metadata_key = keys["metadata"]
        self.signing_key = keys["signing"]
        
        self.private_key_obj, self.public_key_obj = DigitalSignature.generate_keypair()
        
        self.metadata = EncryptedMetadata(self.metadata_key)
        self.merkle_tree = MerkleTree()
        
        private_key_bytes = DigitalSignature.serialize_private_key(self.private_key_obj)
        public_key_bytes = DigitalSignature.serialize_public_key(self.public_key_obj)
        
        encrypted_private_key, nonce_priv = AESGCMEncryption.encrypt_data(
            private_key_bytes,
            self.signing_key
        )
        
        key_info = {
            "salt": salt.hex(),
            "private_key_encrypted": encrypted_private_key.hex(),
            "private_key_nonce": nonce_priv.hex(),
            "public_key": public_key_bytes.hex(),
            "version": 2
        }
        
        self.storage.save_keyinfo(key_info)
        self._save_vault_state()
        
        return True
    
    def unlock_vault(self, password: str) -> bool:
        key_info = self.storage.load_keyinfo()
        if not key_info:
            return False
        
        salt = bytes.fromhex(key_info["salt"])
        
        master_key = KeyDerivation.derive_master_key(password, salt)
        keys = KeyDerivation.derive_keys(master_key)
        
        self.encryption_key = keys["encryption"]
        self.metadata_key = keys["metadata"]
        self.signing_key = keys["signing"]
        
        private_key_enc = bytes.fromhex(key_info["private_key_encrypted"])
        nonce_priv = bytes.fromhex(key_info["private_key_nonce"])
        
        success, private_key_bytes = AESGCMEncryption.decrypt_data(
            private_key_enc,
            self.signing_key,
            nonce_priv
        )
        
        if not success:
            return False
        
        self.private_key_obj = DigitalSignature.deserialize_private_key(private_key_bytes)
        
        public_key_bytes = bytes.fromhex(key_info["public_key"])
        self.public_key_obj = DigitalSignature.deserialize_public_key(public_key_bytes)
        
        self.metadata = EncryptedMetadata(self.metadata_key)
        
        ciphertext, nonce = self.storage.load_metadata()
        if ciphertext and nonce:
            if not self.metadata.decrypt_metadata(ciphertext, nonce):
                return False
        
        merkle_ct, merkle_nonce = self.storage.load_merkle_state()
        if merkle_ct and merkle_nonce:
            success, merkle_data = AESGCMEncryption.decrypt_data(
                merkle_ct,
                self.metadata_key,
                merkle_nonce
            )
            if success:
                merkle_json = json.loads(merkle_data.decode('utf-8'))
                self.merkle_tree = MerkleTree.deserialize(merkle_json)
        
        return True
    
    def store_file(self, file_path: str, password: str) -> tuple:
        if not os.path.exists(file_path):
            return False, "[ERROR] File not found", None
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        file_hash = AESGCMEncryption.compute_file_hash(file_data)
        
        ciphertext, nonce = AESGCMEncryption.encrypt_data(file_data, self.encryption_key)
        
        filename = os.path.basename(file_path)
        file_uuid = self.metadata.add_file(filename, file_hash, len(file_data))
        
        encrypted_package = {
            "ciphertext": ciphertext.hex(),
            "nonce": nonce.hex()
        }
        
        package_json = json.dumps(encrypted_package).encode('utf-8')
        with open(self.storage.get_vault_file_path(file_uuid), 'wb') as f:
            f.write(package_json)
        
        self.merkle_tree.add_file(file_uuid, file_hash)
        
        self._save_vault_state()
        
        return True, f"[OK] File stored with UUID: {file_uuid}", file_uuid
    
    def retrieve_file(self, file_uuid: str, output_path: str = None) -> tuple:
        if not self.storage.file_exists(file_uuid):
            return False, "[ERROR] File not found in vault", None
        
        file_info = self.metadata.get_file_info(file_uuid)
        if not file_info:
            return False, "[ERROR] File metadata not found", None
        
        file_path = self.storage.get_vault_file_path(file_uuid)
        with open(file_path, 'rb') as f:
            package_json = json.load(f)
        
        ciphertext = bytes.fromhex(package_json["ciphertext"])
        nonce = bytes.fromhex(package_json["nonce"])
        
        success, plaintext = AESGCMEncryption.decrypt_data(
            ciphertext,
            self.encryption_key,
            nonce,
            None
        )
        
        if not success:
            return False, "[ERROR] Decryption failed", None
        
        stored_hash = bytes.fromhex(file_info["file_hash"])
        computed_hash = AESGCMEncryption.compute_file_hash(plaintext)
        
        if not TamperingDetection.verify_file_tampering(stored_hash, computed_hash):
            return False, "[ERROR] File integrity check failed - tampering detected", None
        
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(plaintext)
            return True, f"[OK] File retrieved to {output_path}", plaintext
        
        return True, "[OK] File retrieved", plaintext
    
    def verify_vault_integrity(self) -> tuple:
        root_hash = self.merkle_tree.get_root_hash()
        signature = self.storage.load_signature()
        
        if not signature:
            return False, "[WARNING] No signature found"
        
        is_valid = TamperingDetection.check_vault_integrity(
            root_hash,
            signature,
            self.public_key_obj
        )
        
        if is_valid:
            return True, "[OK] Vault integrity verified"
        else:
            return False, "[ERROR] Vault integrity check failed - tampering detected"
    
    def list_files(self) -> list:
        files = []
        for file_uuid in self.metadata.list_files():
            info = self.metadata.get_file_info(file_uuid)
            if info:
                files.append({
                    "uuid": file_uuid,
                    "name": info.get("original_filename"),
                    "size": info.get("file_size"),
                    "uploaded": info.get("uploaded_at")
                })
        return files
    
    def delete_file(self, file_uuid: str) -> bool:
        if not self.storage.file_exists(file_uuid):
            return False
        
        self.storage.delete_file(file_uuid)
        self.metadata.remove_file(file_uuid)
        self.merkle_tree.remove_file(file_uuid)
        self._save_vault_state()
        
        return True
    
    def _save_vault_state(self):
        metadata_ct, metadata_nonce = self.metadata.encrypt_metadata()
        self.storage.save_metadata(metadata_ct, metadata_nonce)
        
        merkle_json = self.merkle_tree.serialize()
        merkle_plaintext = json.dumps(merkle_json).encode('utf-8')
        merkle_ct, merkle_nonce = AESGCMEncryption.encrypt_data(
            merkle_plaintext,
            self.metadata_key
        )
        self.storage.save_merkle_state(merkle_ct, merkle_nonce)
        
        root_hash = self.merkle_tree.get_root_hash()
        if root_hash is None:
            root_hash = b'\x00' * 32
        
        signature = DigitalSignature.sign_data(root_hash, self.private_key_obj)
        self.storage.save_signature(signature)
    
    def get_vault_status(self) -> dict:
        files = self.list_files()
        total_size = sum(f["size"] for f in files)
        
        return {
            "username": self.username,
            "file_count": len(files),
            "total_size": total_size,
            "root_hash": self.merkle_tree.get_root_hash().hex()[:32] + "...",
            "files": files
        }
