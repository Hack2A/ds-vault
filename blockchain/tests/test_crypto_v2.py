import os
import sys
import tempfile
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.key_derivation import KeyDerivation
from src.encryption import AESGCMEncryption, ConstantTimeComparison
from src.signing import DigitalSignature
from src.merkle_tree import MerkleTree
from src.vault_core_v2 import VaultCoreV2
from src.user_manager_v2 import UserManagerV2
from src.security import RateLimiter, TamperingDetection, SecureMemory


class CryptoTestSuite:
    
    def __init__(self):
        self.test_dir = tempfile.mkdtemp()
        self.passed = 0
        self.failed = 0
    
    def print_header(self, test_name):
        print(f"\n{'='*70}")
        print(f"  {test_name}")
        print(f"{'='*70}")
    
    def test_key_derivation(self):
        self.print_header("TEST 1: Key Derivation (Argon2id + HKDF)")
        
        password = "secure_password_123"
        salt = KeyDerivation.generate_salt()
        
        master_key = KeyDerivation.derive_master_key(password, salt)
        
        if len(master_key) != 32:
            print(f"  [FAIL] Master key length: {len(master_key)}, expected 32")
            self.failed += 1
            return
        
        keys = KeyDerivation.derive_keys(master_key)
        
        if len(keys["encryption"]) != 32:
            print(f"  [FAIL] Encryption key length incorrect")
            self.failed += 1
            return
        
        keys2 = KeyDerivation.derive_keys(master_key)
        if keys["encryption"] != keys2["encryption"]:
            print(f"  [FAIL] Derived keys not deterministic")
            self.failed += 1
            return
        
        master_key2 = KeyDerivation.derive_master_key(password, salt)
        if master_key != master_key2:
            print(f"  [FAIL] Same password+salt should produce same key")
            self.failed += 1
            return
        
        master_key3 = KeyDerivation.derive_master_key(password, KeyDerivation.generate_salt())
        if master_key == master_key3:
            print(f"  [FAIL] Different salts should produce different keys")
            self.failed += 1
            return
        
        print(f"  [PASS] Argon2id + HKDF working correctly")
        self.passed += 1
    
    def test_aes_gcm_encryption(self):
        self.print_header("TEST 2: AES-256-GCM Encryption")
        
        key = KeyDerivation.generate_salt(32)
        plaintext = b"This is a secret message for testing"
        
        ciphertext, nonce = AESGCMEncryption.encrypt_data(plaintext, key)
        
        if len(nonce) != 12:
            print(f"  [FAIL] Nonce length: {len(nonce)}, expected 12")
            self.failed += 1
            return
        
        success, decrypted = AESGCMEncryption.decrypt_data(ciphertext, key, nonce)
        
        if not success:
            print(f"  [FAIL] Decryption failed")
            self.failed += 1
            return
        
        if decrypted != plaintext:
            print(f"  [FAIL] Decrypted text doesn't match original")
            self.failed += 1
            return
        
        tampered_ciphertext = bytearray(ciphertext)
        tampered_ciphertext[0] ^= 1
        
        success, _ = AESGCMEncryption.decrypt_data(bytes(tampered_ciphertext), key, nonce)
        
        if success:
            print(f"  [FAIL] Tampered ciphertext should fail authentication")
            self.failed += 1
            return
        
        ciphertext2, nonce2 = AESGCMEncryption.encrypt_data(plaintext, key)
        
        if nonce == nonce2:
            print(f"  [FAIL] Nonces should be random")
            self.failed += 1
            return
        
        print(f"  [PASS] AES-256-GCM with proper nonce handling")
        self.passed += 1
    
    def test_digital_signing(self):
        self.print_header("TEST 3: Ed25519 Digital Signing")
        
        private_key, public_key = DigitalSignature.generate_keypair()
        
        message = b"Important vault state"
        signature = DigitalSignature.sign_data(message, private_key)
        
        if len(signature) != 64:
            print(f"  [FAIL] Signature length: {len(signature)}, expected 64")
            self.failed += 1
            return
        
        is_valid = DigitalSignature.verify_signature(message, signature, public_key)
        
        if not is_valid:
            print(f"  [FAIL] Valid signature not verified")
            self.failed += 1
            return
        
        tampered_message = b"Tampered vault state"
        is_valid = DigitalSignature.verify_signature(tampered_message, signature, public_key)
        
        if is_valid:
            print(f"  [FAIL] Tampered message verified as valid")
            self.failed += 1
            return
        
        private_key2, _ = DigitalSignature.generate_keypair()
        is_valid = DigitalSignature.verify_signature(message, signature, private_key2.public_key())
        
        if is_valid:
            print(f"  [FAIL] Signature verified with wrong key")
            self.failed += 1
            return
        
        print(f"  [PASS] Ed25519 signing and verification working")
        self.passed += 1
    
    def test_merkle_tree(self):
        self.print_header("TEST 4: Merkle Tree Construction")
        
        tree = MerkleTree()
        
        file_hash1 = os.urandom(32)
        file_hash2 = os.urandom(32)
        file_hash3 = os.urandom(32)
        
        tree.add_file("file1", file_hash1)
        tree.add_file("file2", file_hash2)
        tree.add_file("file3", file_hash3)
        
        root_hash = tree.get_root_hash()
        
        if root_hash is None:
            print(f"  [FAIL] Root hash is None")
            self.failed += 1
            return
        
        tree2 = MerkleTree({"file1": file_hash1, "file2": file_hash2, "file3": file_hash3})
        
        if tree.get_root_hash() != tree2.get_root_hash():
            print(f"  [FAIL] Same files should produce same root")
            self.failed += 1
            return
        
        tree.update_file("file1", os.urandom(32))
        
        if tree.get_root_hash() == root_hash:
            print(f"  [FAIL] Root should change after file update")
            self.failed += 1
            return
        
        tree.remove_file("file1")
        
        if "file1" in tree.file_hashes:
            print(f"  [FAIL] File not removed")
            self.failed += 1
            return
        
        print(f"  [PASS] Merkle tree working correctly")
        self.passed += 1
    
    def test_rate_limiting(self):
        self.print_header("TEST 5: Rate Limiting")
        
        limiter = RateLimiter(max_attempts=3, lockout_time=1)
        
        for i in range(3):
            try:
                limiter.record_failure("user1")
            except PermissionError:
                if i < 2:
                    print(f"  [FAIL] Locked too early")
                    self.failed += 1
                    return
        
        try:
            limiter.record_failure("user1")
            print(f"  [FAIL] Should be locked")
            self.failed += 1
            return
        except PermissionError:
            pass
        
        import time
        time.sleep(1.5)
        
        if limiter.is_locked("user1"):
            print(f"  [FAIL] Should be unlocked after lockout time")
            self.failed += 1
            return
        
        limiter.record_failure("user1")
        limiter.record_failure("user1")
        
        remaining = limiter.get_remaining_lockout("user1")
        if remaining <= 0:
            remaining = limiter.get_remaining_lockout("user1")
        
        print(f"  [PASS] Rate limiting working correctly")
        self.passed += 1
    
    def test_constant_time_comparison(self):
        self.print_header("TEST 6: Constant-Time Comparison")
        
        data1 = b"secret_data_12345"
        data2 = b"secret_data_12345"
        data3 = b"different_data123"
        
        result1 = ConstantTimeComparison.compare_bytes(data1, data2)
        if not result1:
            print(f"  [FAIL] Same data should be equal")
            self.failed += 1
            return
        
        result2 = ConstantTimeComparison.compare_bytes(data1, data3)
        if result2:
            print(f"  [FAIL] Different data should not be equal")
            self.failed += 1
            return
        
        result3 = ConstantTimeComparison.compare_strings("password", "password")
        if not result3:
            print(f"  [FAIL] Same strings should be equal")
            self.failed += 1
            return
        
        result4 = ConstantTimeComparison.compare_strings("password", "wrongpass")
        if result4:
            print(f"  [FAIL] Different strings should not be equal")
            self.failed += 1
            return
        
        print(f"  [PASS] Constant-time comparison working")
        self.passed += 1
    
    def test_vault_operations(self):
        self.print_header("TEST 7: Vault V2 Operations")
        
        vault_path = os.path.join(self.test_dir, "test_vault")
        vault = VaultCoreV2("testuser", vault_path)
        
        password = "test_password_secure_123"
        vault.initialize_vault(password)
        
        test_file = os.path.join(self.test_dir, "test_doc.txt")
        with open(test_file, 'w') as f:
            f.write("Test document content for vault storage")
        
        success, msg, file_uuid = vault.store_file(test_file, password)
        if not success:
            print(f"  [FAIL] File storage failed: {msg}")
            self.failed += 1
            return
        
        files = vault.list_files()
        if len(files) != 1:
            print(f"  [FAIL] File not listed correctly")
            self.failed += 1
            return
        
        output_file = os.path.join(self.test_dir, "retrieved_doc.txt")
        success, msg, data = vault.retrieve_file(file_uuid, output_file)
        if not success:
            print(f"  [FAIL] File retrieval failed: {msg}")
            self.failed += 1
            return
        
        if not os.path.exists(output_file):
            print(f"  [FAIL] Output file not created")
            self.failed += 1
            return
        
        with open(output_file, 'rb') as f:
            retrieved_content = f.read()
        
        with open(test_file, 'rb') as f:
            original_content = f.read()
        
        if retrieved_content != original_content:
            print(f"  [FAIL] Retrieved content doesn't match original")
            self.failed += 1
            return
        
        is_valid, msg = vault.verify_vault_integrity()
        if not is_valid:
            print(f"  [FAIL] Vault integrity check failed: {msg}")
            self.failed += 1
            return
        
        success = vault.delete_file(file_uuid)
        if not success:
            print(f"  [FAIL] File deletion failed")
            self.failed += 1
            return
        
        files_after = vault.list_files()
        if len(files_after) != 0:
            print(f"  [FAIL] File not deleted")
            self.failed += 1
            return
        
        print(f"  [PASS] Vault V2 operations working correctly")
        self.passed += 1
    
    def test_user_management(self):
        self.print_header("TEST 8: User Management V2")
        
        users_dir = os.path.join(self.test_dir, "users")
        manager = UserManagerV2(users_dir)
        
        success, msg, seed_phrase = manager.register_user("alice")
        if not success:
            print(f"  [FAIL] User registration failed: {msg}")
            self.failed += 1
            return
        
        if len(seed_phrase) != 12:
            print(f"  [FAIL] Seed phrase length incorrect: {len(seed_phrase)}")
            self.failed += 1
            return
        
        users = manager.list_users()
        if "alice" not in users:
            print(f"  [FAIL] User not in list")
            self.failed += 1
            return
        
        success, msg, _ = manager.register_user("alice")
        if success:
            print(f"  [FAIL] Should not allow duplicate registration")
            self.failed += 1
            return
        
        success, msg = manager.login_user("alice", seed_phrase)
        if not success:
            print(f"  [FAIL] Login failed with correct seed phrase: {msg}")
            self.failed += 1
            return
        
        wrong_phrase = ["wrong"] * 12
        success, msg = manager.login_user("alice", wrong_phrase)
        
        print(f"  [PASS] User management V2 working correctly")
        self.passed += 1
    
    def run_all_tests(self):
        print("\n" + "=" * 70)
        print("  CRYPTOGRAPHIC VAULT V2 - COMPREHENSIVE TEST SUITE")
        print("=" * 70)
        
        self.test_key_derivation()
        self.test_aes_gcm_encryption()
        self.test_digital_signing()
        self.test_merkle_tree()
        self.test_rate_limiting()
        self.test_constant_time_comparison()
        self.test_vault_operations()
        self.test_user_management()
        
        print("\n" + "=" * 70)
        print(f"  RESULTS: {self.passed} PASSED, {self.failed} FAILED")
        print("=" * 70 + "\n")
        
        return self.failed == 0


if __name__ == "__main__":
    suite = CryptoTestSuite()
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)
