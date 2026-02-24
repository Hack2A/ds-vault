import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.user_manager import UserManager
from src.vault_core import VaultCore


class SecureVaultApp:
    def __init__(self):
        self.user_manager = UserManager("vault_users")
        self.current_user = None
        self.vault = None

    def print_banner(self):
        print("\n" + "#" * 60)
        print("  BLOCKCHAIN-SECURED FILE VAULT")
        print("  Encrypt, Store & Verify with Blockchain")
        print("#" * 60 + "\n")

    def print_menu(self):
        print("\n" + "=" * 60)
        print("  MAIN MENU")
        print("=" * 60)
        if self.current_user:
            print(f"  Logged in: {self.current_user}\n")
            print("  1. Store file     2. Retrieve file   3. List files")
            print("  4. Verify file    5. Vault status    6. Logout")
            print("  0. Exit")
        else:
            print("\n  1. Register       2. Login           3. List users")
            print("  0. Exit")
        print("=" * 60)

    def register_user(self):
        username = input("  Username: ").strip()
        if not username:
            print("  [ERROR] Username empty")
            return
        
        success, msg, seed_phrase = self.user_manager.register_user(username)
        
        if success:
            print(f"\n  {msg}")
            print(f"\n  Seed phrase (SAVE THIS):")
            for i, word in enumerate(seed_phrase, 1):
                print(f"    {i:>2}. {word}")
            input("\n  Press Enter when saved...")
        else:
            print(f"  {msg}")

    def login_user(self):
        username = input("  Username: ").strip()
        users = self.user_manager.list_users()
        
        if username not in users:
            print(f"  [ERROR] User not found")
            return
        
        print(f"\n  Enter 12-word seed phrase (space-separated)")
        phrase_input = input("  > ").strip().lower()
        seed_phrase = phrase_input.split()
        
        if len(seed_phrase) != 12:
            print(f"  [ERROR] Must enter 12 words")
            return
        
        success, msg = self.user_manager.login_user(username, seed_phrase)
        
        if success:
            print(f"\n  {msg}")
            self.current_user = username
            vault_dir = self.user_manager.get_user_vault_dir(username)
            self.vault = VaultCore(username, vault_dir, difficulty=3)
            print(f"  Vault initialized")
        else:
            print(f"  {msg}")

    def store_file(self):
        if not self.current_user:
            print("  [ERROR] Not logged in")
            return
        
        file_path = input("  File path: ").strip()
        if not os.path.exists(file_path):
            print(f"  [ERROR] File not found")
            return
        
        password = input("  Seed phrase: ").strip()
        success, msg, file_hash = self.vault.store_file(file_path, password)
        print(f"\n  {msg}")

    def retrieve_file(self):
        if not self.current_user:
            print("  [ERROR] Not logged in")
            return
        
        files = self.vault.list_files()
        if not files:
            print("  No files in vault")
            return
        
        print("  Available files:")
        for i, fname in enumerate(files, 1):
            info = self.vault.get_file_info(fname)
            size_kb = info.get("file_size", 0) / 1024
            print(f"    {i}. {fname} ({size_kb:.2f} KB)")
        
        file_idx = input("\n  Select (number): ").strip()
        try:
            idx = int(file_idx) - 1
            if not (0 <= idx < len(files)):
                print("  [ERROR] Invalid selection")
                return
            file_name = files[idx]
        except:
            print("  [ERROR] Invalid input")
            return
        
        password = input("  Seed phrase: ").strip()
        output_path = input("  Output path (press Enter to skip): ").strip() or None
        
        success, msg, file_data = self.vault.retrieve_file(file_name, password, output_path)
        print(f"\n  {msg}")

    def list_files(self):
        if not self.current_user:
            print("  [ERROR] Not logged in")
            return
        
        files = self.vault.list_files()
        if not files:
            print("  Vault is empty")
            return
        
        for i, fname in enumerate(files, 1):
            info = self.vault.get_file_info(fname)
            size_kb = info.get("file_size", 0) / 1024
            stored = info.get("stored_at", "")[:10]
            print(f"  {i}. {fname:<30} ({size_kb:>8.2f} KB)  [{stored}]")

    def verify_integrity(self):
        if not self.current_user:
            print("  [ERROR] Not logged in")
            return
        
        files = self.vault.list_files()
        if not files:
            print("  No files in vault")
            return
        
        print("  Select file to verify:")
        for i, fname in enumerate(files, 1):
            print(f"    {i}. {fname}")
        
        file_idx = input("\n  Select (number): ").strip()
        try:
            idx = int(file_idx) - 1
            if not (0 <= idx < len(files)):
                print("  [ERROR] Invalid selection")
                return
            file_name = files[idx]
        except:
            print("  [ERROR] Invalid input")
            return
        
        valid, msg = self.vault.verify_file_integrity(file_name)
        print(f"\n  {msg}")

    def view_vault_status(self):
        if not self.current_user:
            print("  [ERROR] Not logged in")
            return
        self.vault.display_vault_status()

    def list_users(self):
        users = self.user_manager.list_users()
        if not users:
            print("  No users")
        else:
            for i, user in enumerate(users, 1):
                print(f"    {i}. {user}")

    def logout_user(self):
        print(f"\n  Logging out {self.current_user}...")
        self.current_user = None
        self.vault = None

    def run(self):
        self.print_banner()
        
        while True:
            self.print_menu()
            choice = input("  Choice: ").strip()
            
            if not self.current_user:
                if choice == "1":
                    self.register_user()
                elif choice == "2":
                    self.login_user()
                elif choice == "3":
                    self.list_users()
                elif choice == "0":
                    print("\n  Goodbye!")
                    break
            else:
                if choice == "1":
                    self.store_file()
                elif choice == "2":
                    self.retrieve_file()
                elif choice == "3":
                    self.list_files()
                elif choice == "4":
                    self.verify_integrity()
                elif choice == "5":
                    self.view_vault_status()
                elif choice == "6":
                    self.logout_user()
                elif choice == "0":
                    print("\n  Goodbye!")
                    break


if __name__ == "__main__":
    app = SecureVaultApp()
    app.run()
