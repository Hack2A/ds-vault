import os
import sys
from src.user_manager_v2 import UserManagerV2


class SecureVaultV2CLI:
    
    def __init__(self):
        self.user_manager = UserManagerV2()
        self.current_user = None
        self.current_vault = None
    
    def print_banner(self):
        print("\n" + "=" * 60)
        print("  SECURE FILE VAULT V2")
        print("  Cryptographically Secure Local Encryption")
        print("=" * 60 + "\n")
    
    def print_menu(self):
        print("\n" + "=" * 60)
        print("  MAIN MENU")
        print("=" * 60)
        if self.current_user:
            print(f"  Logged in: {self.current_user}\n")
            print("  1. Store file     2. Retrieve file   3. List files")
            print("  4. Verify file    5. Vault status    6. Check integrity")
            print("  7. Delete file    8. Logout          0. Exit")
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
            print(f"\n  SAVE THIS 12-WORD SEED PHRASE:")
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
            self.current_vault = self.user_manager.get_user_vault(username)
            self.current_vault.unlock_vault(' '.join(seed_phrase))
            print(f"  Vault unlocked")
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
        
        success, msg, file_uuid = self.current_vault.store_file(file_path, "")
        print(f"\n  {msg}")
    
    def retrieve_file(self):
        if not self.current_user:
            print("  [ERROR] Not logged in")
            return
        
        files = self.current_vault.list_files()
        if not files:
            print("  No files in vault")
            return
        
        print("  Available files:")
        for i, f in enumerate(files, 1):
            size_kb = f["size"] / 1024
            print(f"    {i}. {f['name']} ({size_kb:.2f} KB)")
        
        file_idx = input("\n  Select (number): ").strip()
        try:
            idx = int(file_idx) - 1
            if not (0 <= idx < len(files)):
                print("  [ERROR] Invalid selection")
                return
            file_uuid = files[idx]["uuid"]
        except:
            print("  [ERROR] Invalid input")
            return
        
        output_path = input("  Output path (press Enter to skip): ").strip() or None
        
        success, msg, file_data = self.current_vault.retrieve_file(file_uuid, output_path)
        print(f"\n  {msg}")
    
    def list_files(self):
        if not self.current_user:
            print("  [ERROR] Not logged in")
            return
        
        files = self.current_vault.list_files()
        if not files:
            print("  Vault is empty")
            return
        
        print("\n  Files in vault:")
        for i, f in enumerate(files, 1):
            size_kb = f["size"] / 1024
            print(f"  {i}. {f['name']:<30} ({size_kb:>8.2f} KB)  {f['uploaded'][:10]}")
    
    def verify_file(self):
        if not self.current_user:
            print("  [ERROR] Not logged in")
            return
        
        files = self.current_vault.list_files()
        if not files:
            print("  No files in vault")
            return
        
        print("  Select file to verify:")
        for i, f in enumerate(files, 1):
            print(f"    {i}. {f['name']}")
        
        file_idx = input("\n  Select (number): ").strip()
        try:
            idx = int(file_idx) - 1
            if not (0 <= idx < len(files)):
                print("  [ERROR] Invalid selection")
                return
            file_uuid = files[idx]["uuid"]
        except:
            print("  [ERROR] Invalid input")
            return
        
        success, msg, _ = self.current_vault.retrieve_file(file_uuid)
        if success:
            print(f"\n  [OK] File integrity verified")
        else:
            print(f"\n  {msg}")
    
    def check_vault_integrity(self):
        if not self.current_user:
            print("  [ERROR] Not logged in")
            return
        
        is_valid, msg = self.current_vault.verify_vault_integrity()
        print(f"\n  {msg}")
    
    def delete_file(self):
        if not self.current_user:
            print("  [ERROR] Not logged in")
            return
        
        files = self.current_vault.list_files()
        if not files:
            print("  No files in vault")
            return
        
        print("  Select file to delete:")
        for i, f in enumerate(files, 1):
            print(f"    {i}. {f['name']}")
        
        file_idx = input("\n  Select (number): ").strip()
        try:
            idx = int(file_idx) - 1
            if not (0 <= idx < len(files)):
                print("  [ERROR] Invalid selection")
                return
            file_uuid = files[idx]["uuid"]
        except:
            print("  [ERROR] Invalid input")
            return
        
        confirm = input(f"  Permanently delete {files[idx]['name']}? (yes/no): ").strip().lower()
        if confirm == "yes":
            if self.current_vault.delete_file(file_uuid):
                print("  [OK] File deleted")
            else:
                print("  [ERROR] Deletion failed")
    
    def view_vault_status(self):
        if not self.current_user:
            print("  [ERROR] Not logged in")
            return
        
        status = self.current_vault.get_vault_status()
        print("\n" + "=" * 60)
        print("  VAULT STATUS")
        print("=" * 60)
        print(f"  User            : {status['username']}")
        print(f"  Files in Vault  : {status['file_count']}")
        print(f"  Total Size      : {status['total_size']/1024:.2f} KB")
        print(f"  Merkle Root     : {status['root_hash']}")
        print("=" * 60 + "\n")
    
    def list_users(self):
        users = self.user_manager.list_users()
        if not users:
            print("  No users")
        else:
            print("\n  Registered users:")
            for i, user in enumerate(users, 1):
                print(f"    {i}. {user}")
    
    def logout_user(self):
        if self.current_user:
            print(f"\n  Logging out {self.current_user}...")
            self.current_user = None
            self.current_vault = None
    
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
                    print("  [ERROR] Invalid choice")
            else:
                if choice == "1":
                    self.store_file()
                elif choice == "2":
                    self.retrieve_file()
                elif choice == "3":
                    self.list_files()
                elif choice == "4":
                    self.verify_file()
                elif choice == "5":
                    self.view_vault_status()
                elif choice == "6":
                    self.check_vault_integrity()
                elif choice == "7":
                    self.delete_file()
                elif choice == "8":
                    self.logout_user()
                elif choice == "0":
                    print("\n  Goodbye!")
                    break
                else:
                    print("  [ERROR] Invalid choice")


if __name__ == "__main__":
    app = SecureVaultV2CLI()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n\n  Interrupted by user")
        sys.exit(0)
