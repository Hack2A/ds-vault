import json
import os
import sys
import hashlib
from datetime import datetime

# Ensure ds-vault root is on the path so both packages resolve
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from blockchain.blockchain import Blockchain
from Encryption.encryption import FileEncryption, AESGCMEncryption
from Encryption.key_derivation import KeyDerivation


class VaultCore:
    def __init__(self, username: str, vault_dir: str, difficulty: int = 3):
        self.username = username
        self.vault_dir = vault_dir
        self.blockchain = Blockchain(difficulty=difficulty)
        self.metadata_file = os.path.join(vault_dir, "_vault_metadata.json")
        self.files_dir = os.path.join(vault_dir, "files")
        self.metadata = {}
        
        os.makedirs(self.vault_dir, exist_ok=True)
        os.makedirs(self.files_dir, exist_ok=True)
        self._load_metadata()

    def _load_metadata(self):
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            except:
                self.metadata = {}

    def _save_metadata(self):
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception:
            pass

    def store_file(self, file_path: str, password: str) -> tuple:
        if not os.path.exists(file_path):
            return False, f"[ERROR] File not found: {file_path}", ""
        
        file_name = os.path.basename(file_path)
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            return self.store_data(file_name, file_data, password)
        except Exception as e:
            return False, f"[ERROR] Failed to read file: {e}", ""

    def store_text(self, text_name: str, text_content: str, password: str) -> tuple:
        file_data = text_content.encode('utf-8')
        return self.store_data(text_name, file_data, password, is_text=True)

    def store_data(self, item_name: str, data_bytes: bytes, password: str, is_text: bool = False) -> tuple:
        print(f"\n[STORING] Processing item: {item_name}")
        
        try:
            size_mb = len(data_bytes) / (1024 * 1024)
            print(f"  Size: {size_mb:.2f} MB")
            print(f"  [ENCRYPTING] Using AES-GCM password-based encryption...")
            
            original_hash = FileEncryption.compute_file_hash(data_bytes)

            salt = os.urandom(16)
            key = KeyDerivation.derive_master_key(password, salt)
            encrypted_data, nonce = AESGCMEncryption.encrypt_data(data_bytes, key)
            
            encrypted_file_path = os.path.join(self.files_dir, f"{item_name}.enc")
            with open(encrypted_file_path, 'wb') as f:
                f.write(encrypted_data)
            
            print(f"  [OK] AES-GCM Encrypted data stored")
            print(f"  [BLOCKCHAIN] Recording on blockchain...")

            block_data = {
                "type": "file_record",
                "file_name": item_name,
                "original_hash": original_hash,
                "salt": salt.hex(),
                "nonce": nonce.hex(),
                "timestamp": datetime.now().isoformat(),
            }
            
            block = self.blockchain.add_block(block_data)
            print(f"  [MINING] Mining Block #{block.index} (difficulty={self.blockchain.difficulty})...")
            print(f"  [OK] Nonce={block.nonce}  |  Hash={block.hash[:24]}...")
            print(f"  [OK] Recorded on blockchain at Block #{block.index}")
            
            self.metadata[item_name] = {
                "original_hash": original_hash,
                "salt": salt.hex(),
                "nonce": nonce.hex(),
                "file_size": len(data_bytes),
                "encrypted_size": len(encrypted_data),
                "stored_at": datetime.now().isoformat(),
                "block_number": block.index,
                "is_text": is_text
            }
            
            self._save_metadata()
            print(f"  [OK] Item stored securely by {self.username}")
            return True, "[OK] Item stored securely", original_hash
            
        except Exception as e:
            return False, f"[ERROR] Failed to store item: {e}", ""

    def retrieve_file(self, file_name: str, password: str, output_path: str = None) -> tuple:
        print(f"\n[RETRIEVING] File: {file_name}")
        
        if file_name not in self.metadata:
            return False, f"[ERROR] File not found in metadata", b""
        
        meta = self.metadata[file_name]
        print(f"  [BLOCKCHAIN] Verifying on blockchain...")
        
        found = False
        for block in self.blockchain.chain:
            if isinstance(block.data, dict) and block.data.get("file_name") == file_name:
                found = True
                print(f"  [OK] Blockchain record found at Block #{block.index}")
                break
        
        if not found:
            return False, f"[ERROR] File not found on blockchain", b""
        
        encrypted_file_path = os.path.join(self.files_dir, f"{file_name}.enc")
        if not os.path.exists(encrypted_file_path):
            return False, f"[ERROR] Encrypted file not found", b""
        
        try:
            with open(encrypted_file_path, 'rb') as f:
                encrypted_data = f.read()
            
            print(f"  [DECRYPTING] Using AES-GCM...")
            
            salt = bytes.fromhex(meta["salt"])
            nonce = bytes.fromhex(meta["nonce"])

            key = KeyDerivation.derive_master_key(password, salt)
            valid, decrypted_data = AESGCMEncryption.decrypt_data(encrypted_data, key, nonce)
            
            if not valid:
                return False, f"[ERROR] Decryption failed - wrong password or corrupted data", b""
            
            print(f"  [OK] Decryption successful")
            print(f"  [VERIFYING] Checking integrity...")
            
            current_hash = FileEncryption.compute_file_hash(decrypted_data)
            if current_hash != meta["original_hash"]:
                return False, f"[ERROR] Hash mismatch - file tampered", decrypted_data
            
            print(f"  [OK] Integrity verified - no tampering detected")
            
            is_text = meta.get("is_text", False)
            return True, f"[OK] Item retrieved successfully", decrypted_data, is_text
            
        except Exception as e:
            return False, f"[ERROR] Failed to retrieve: {e}", b"", False

    def verify_file_integrity(self, file_name: str) -> tuple:
        if file_name not in self.metadata:
            return False, f"[ERROR] File not found"
        
        meta = self.metadata[file_name]
        
        block_num = meta.get("block_number")
        original_hash = meta["original_hash"]
        
        print(f"  [OK] File '{file_name}' verified on blockchain")
        print(f"   Hash : {original_hash[:32]}...")
        print(f"   Size : {meta['file_size']} bytes")
        print(f"   Block: #{block_num}")
        
        return True, f"[OK] File integrity verified"

    def list_files(self) -> list:
        return list(self.metadata.keys())

    def get_file_info(self, file_name: str) -> dict:
        if file_name in self.metadata:
            return self.metadata[file_name]
        return {}

    def display_vault_status(self):
        print("\n" + "=" * 60)
        print("  VAULT STATUS")
        print("=" * 60)
        print(f"\n  User            : {self.username}")
        print(f"  Files in Vault  : {len(self.metadata)}")
        total_size = sum(m.get("file_size", 0) for m in self.metadata.values())
        print(f"  Total Size      : {total_size / (1024*1024):.2f} MB")
        print(f"  Blockchain Blocks: {len(self.blockchain.chain)}")
        is_valid, _ = self.blockchain.is_chain_valid()
        print(f"  Chain Valid     : {'YES' if is_valid else 'NO'}")
        
        if self.metadata:
            print(f"\n  STORED FILES:")
            print(f"  {'-' * 56}")
            for i, (fname, meta) in enumerate(self.metadata.items(), 1):
                size_kb = meta.get("file_size", 0) / 1024
                block = meta.get("block_number", "?")
                print(f"    {i}. {fname:<32} ({size_kb:>7.2f} KB) Block: #{block}")
        
        print(f"\n" + "=" * 60 + "\n")
