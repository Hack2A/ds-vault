import os
import sys
import tempfile
import shutil


_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

from Encryption.user_manager import UserManager
from Encryption.vault_core import VaultCore


class VaultTestSuite:
    def __init__(self):
        self.test_dir = tempfile.mkdtemp()
        self.user_manager = UserManager(os.path.join(self.test_dir, "users"))
        self.test_files = []
        print("\n" + "=" * 70)
        print("  BLOCKCHAIN VAULT TEST SUITE")
        print("=" * 70)

    def create_test_file(self, name, content):
        path = os.path.join(self.test_dir, name)
        with open(path, 'w') as f:
            f.write(content)
        self.test_files.append((name, path))
        return path

    def cleanup(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_user_registration(self):
        print("\n[TEST 1] User Registration")
        print("-" * 70)
        
        success, msg, seed_alice = self.user_manager.register_user("alice")
        assert success, f"Alice registration failed: {msg}"
        print(f"  [OK] Alice registered")
        
        success, msg, seed_bob = self.user_manager.register_user("bob")
        assert success, f"Bob registration failed: {msg}"
        print(f"  [OK] Bob registered")
        
        users = self.user_manager.list_users()
        assert "alice" in users and "bob" in users
        print(f"  [OK] Both users registered: {users}")
        
        return seed_alice, seed_bob

    def test_file_storage(self, alice_vault, bob_vault):
        print("\n[TEST 2] File Storage and Encryption")
        print("-" * 70)
        
        test_text_path = self.create_test_file("test_document.txt", "This is a confidential document.\nIt should be encrypted and stored on the blockchain.")
        test_data_path = self.create_test_file("test_data.txt", "Important data: " + "X" * 1000)
        
        password = "test_password_123"
        
        print("\n  Alice storing file...")
        success, msg, file_hash = alice_vault.store_file(test_text_path, password)
        assert success
        print(f"  [OK] File stored by Alice")
        
        print("\n  Bob storing file...")
        success, msg, file_hash = bob_vault.store_file(test_data_path, password)
        assert success
        print(f"  [OK] File stored by Bob")
        
        alice_files = alice_vault.list_files()
        bob_files = bob_vault.list_files()
        
        assert len(alice_files) == 1
        assert len(bob_files) == 1
        print(f"\n  [OK] Vault isolation verified")

    def test_file_retrieval(self, alice_vault, bob_vault):
        print("\n[TEST 3] File Retrieval and Decryption")
        print("-" * 70)
        
        password = "test_password_123"
        alice_files = alice_vault.list_files()
        
        if alice_files:
            alice_file = alice_files[0]
            output_path = os.path.join(self.test_dir, f"retrieved_{alice_file}")
            
            print(f"\n  Retrieving Alice's file: {alice_file}")
            success, msg, data = alice_vault.retrieve_file(alice_file, password, output_path)
            assert success
            print(f"  [OK] File retrieved and decrypted")

    def test_integrity_verification(self, alice_vault):
        print("\n[TEST 4] File Integrity Verification")
        print("-" * 70)
        
        files = alice_vault.list_files()
        if files:
            file_name = files[0]
            print(f"\n  Verifying file: {file_name}")
            valid, msg = alice_vault.verify_file_integrity(file_name)
            print(f"  {msg}")
            assert valid

    def test_blockchain_records(self, alice_vault):
        print("\n[TEST 5] Blockchain Records")
        print("-" * 70)
        
        blockchain = alice_vault.blockchain
        print(f"\n  Blockchain state:")
        print(f"    Chain length: {len(blockchain.chain)}")
        print(f"    Difficulty: {blockchain.difficulty}")
        
        is_valid, msg = blockchain.is_chain_valid()
        print(f"\n  Chain validity: {'VALID' if is_valid else 'INVALID'}")
        assert is_valid

    def test_multiple_file_storage(self, alice_vault):
        print("\n[TEST 6] Multiple File Storage")
        print("-" * 70)
        
        password = "test_password_123"
        files_to_store = [
            ("document1.txt", "Content 1\n" * 10),
            ("document2.txt", "Content 2\n" * 10),
        ]
        
        print(f"\n  Storing {len(files_to_store)} files...")
        for fname, content in files_to_store:
            fpath = self.create_test_file(fname, content)
            success, msg, fhash = alice_vault.store_file(fpath, password)
            assert success
            print(f"    [OK] {fname}")

    def test_vault_status(self, alice_vault):
        print("\n[TEST 7] Vault Status Report")
        print("-" * 70)
        alice_vault.display_vault_status()
        print(f"  [OK] Vault status displayed")

    def run_all_tests(self):
        try:
            seed_alice, seed_bob = self.test_user_registration()
            
            vault_dir_alice = self.user_manager.get_user_vault_dir("alice")
            vault_dir_bob = self.user_manager.get_user_vault_dir("bob")
            
            alice_vault = VaultCore("alice", vault_dir_alice, difficulty=2)
            bob_vault = VaultCore("bob", vault_dir_bob, difficulty=2)
            
            self.test_file_storage(alice_vault, bob_vault)
            self.test_file_retrieval(alice_vault, bob_vault)
            self.test_integrity_verification(alice_vault)
            self.test_blockchain_records(alice_vault)
            self.test_multiple_file_storage(alice_vault)
            self.test_vault_status(alice_vault)
            
            print("\n" + "=" * 70)
            print("  ALL TESTS PASSED!")
            print("=" * 70 + "\n")
            return True
            
        except Exception as e:
            print(f"\n  [ERROR] Test failed: {e}")
            return False
        
        finally:
            self.cleanup()


if __name__ == "__main__":
    suite = VaultTestSuite()
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)
