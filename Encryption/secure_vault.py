import os
import sys

# Add ds-vault root to path so 'Encryption' and 'blockchain' packages resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Go one level up from Encryption/ to reach ds-vault/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Encryption.user_manager import UserManager
from Encryption.vault_core import VaultCore

class SecureVaultApp:
    def __init__(self):
        # users are stored in a vault_users/ folder relative to Encryption/
        users_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vault_users")
        self.user_manager = UserManager(users_dir)
        self.current_user = None
        self.vault = None

    def print_banner(self):
        print("\n" + "#" * 60)
        print("  SECURE VAULT  |  AES-GCM Encryption + Blockchain Integrity")
        print("  Files encrypted at rest. Integrity logged on-chain.")
        print("#" * 60 + "\n")

    def print_menu(self):
        print("\n" + "=" * 60)
        print("  MAIN MENU")
        print("=" * 60)
        if self.current_user:
            print(f"  Logged in: {self.current_user}\n")
            print("  1. Store file     2. Store text      3. Retrieve")
            print("  4. List items     5. Verify integrity")
            print("  6. Vault status   7. Logout          0. Exit")
        else:
            print("\n  1. Register       2. Login           3. List users")
            print("  0. Exit")
        print("=" * 60)

    def register_user(self):
        username = input("  Username: ").strip()
        if not username:
            print("  [ERROR] Username cannot be empty")
            return
        success, msg, seed_phrase = self.user_manager.register_user(username)
        if success:
            print(f"\n  {msg}")
            print(f"\n  YOUR 12-WORD SEED PHRASE (SAVE THIS SECURELY):")
            for i, word in enumerate(seed_phrase, 1):
                print(f"    {i:>2}. {word}")
            input("\n  Press Enter once you have saved your seed phrase...")
        else:
            print(f"  {msg}")

    def login_user(self):
        username = input("  Username: ").strip()
        users = self.user_manager.list_users()
        if username not in users:
            print("  [ERROR] User not found")
            return
        print(f"\n  Enter your 12-word seed phrase (space-separated):")
        phrase_input = input("  > ").strip().lower()
        seed_phrase = phrase_input.split()
        if len(seed_phrase) != 12:
            print("  [ERROR] Must enter exactly 12 words")
            return
        success, msg = self.user_manager.login_user(username, seed_phrase)
        if success:
            print(f"\n  {msg}")
            self.current_user = username
            vault_dir = self.user_manager.get_user_vault_dir(username)
            self.vault = VaultCore(username, vault_dir, difficulty=3)
            print("  Vault loaded successfully.")
        else:
            print(f"  {msg}")

    def _pick_mode(self) -> str:
        print("\n  Select storage mode:")
        print("    1. Normal   — AES-GCM encryption only")
        print("    2. Advanced — AES-GCM encryption + Blockchain integrity record")
        choice = input("  Mode (1/2, default=2): ").strip()
        return "normal" if choice == "1" else "advanced"

    def store_file(self):
        if not self.current_user:
            print("  [ERROR] Not logged in")
            return
        file_path = input("  File path to store: ").strip()
        if not os.path.exists(file_path):
            print("  [ERROR] File not found")
            return
        mode = self._pick_mode()
        if mode == "normal":
            password = ""
        else:
            password = input("  Seed phrase (used as encryption key): ").strip()
        success, msg, _ = self.vault.store_file(file_path, password, mode=mode)
        print(f"\n  {msg}")

    def store_text(self):
        if not self.current_user:
            print("  [ERROR] Not logged in")
            return
            
        text_name = input("  Text item name (e.g. 'secret_note'): ").strip()
        if not text_name:
            print("  [ERROR] Name cannot be empty")
            return
            
        print("  Enter your confidential text (Type ':wq' on a new line and press Enter to save):")
        lines = []
        while True:
            line = input("  > ")
            if line.strip() == ":wq":
                break
            lines.append(line)
            
        text_content = "\n".join(lines)
        if not text_content:
            print("  [ERROR] Text cannot be empty")
            return
            
        mode = self._pick_mode()
        if mode == "normal":
            password = ""
        else:
            password = input("  Seed phrase (used as encryption key): ").strip()
        success, msg, _ = self.vault.store_text(text_name, text_content, password, mode=mode)
        print(f"\n  {msg}")

    def retrieve_file(self):
        if not self.current_user:
            print("  [ERROR] Not logged in")
            return
        files = self.vault.list_files()
        if not files:
            print("  Vault is empty")
            return
        print("\n  Files in vault:")
        for i, fname in enumerate(files, 1):
            info = self.vault.get_file_info(fname)
            size_kb = info.get("file_size", 0) / 1024
            print(f"    {i}. {fname:<30} ({size_kb:>8.2f} KB)")
        file_idx = input("\n  Select file (number): ").strip()
        try:
            idx = int(file_idx) - 1
            if not (0 <= idx < len(files)):
                print("  [ERROR] Invalid selection")
                return
            file_name = files[idx]
        except ValueError:
            print("  [ERROR] Invalid input")
            return
        info = self.vault.get_file_info(file_name)
        is_text = info.get("is_text", False)
        mode = info.get("mode", "advanced")
        
        if mode == "normal":
            password = ""  # key is stored in metadata, no credential needed
        else:
            password = input("  Seed phrase: ").strip()
        
        output_path = None
        if not is_text:
            output_path = input("  Output path (Enter to skip): ").strip() or None
            
        success, msg, decrypted_data, is_text_retrieved = self.vault.retrieve_file(file_name, password, output_path)
        print(f"\n  {msg}")
        
        if success and is_text_retrieved:
            print("\n  [ DECRYPTED TEXT ]:")
            print("-" * 60)
            print(decrypted_data.decode('utf-8'))
            print("-" * 60)

    def list_files(self):
        if not self.current_user:
            print("  [ERROR] Not logged in")
            return
        files = self.vault.list_files()
        if not files:
            print("  Vault is empty")
            return
        print("\n  Files in vault:")
        for i, fname in enumerate(files, 1):
            info = self.vault.get_file_info(fname)
            size_kb = info.get("file_size", 0) / 1024
            stored = info.get("stored_at", "")[:10]
            block = info.get("block_number", "?")
            print(f"  {i}. {fname:<30} ({size_kb:>8.2f} KB)  [{stored}]  Block #{block}")

    def verify_integrity(self):
        if not self.current_user:
            print("  [ERROR] Not logged in")
            return
        files = self.vault.list_files()
        if not files:
            print("  No files in vault")
            return
        print("\n  Select file to verify:")
        for i, fname in enumerate(files, 1):
            print(f"    {i}. {fname}")
        file_idx = input("\n  Select (number): ").strip()
        try:
            idx = int(file_idx) - 1
            if not (0 <= idx < len(files)):
                print("  [ERROR] Invalid selection")
                return
            file_name = files[idx]
        except ValueError:
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
            print("  No registered users")
        else:
            print("\n  Registered users:")
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
                    print("  [ERROR] Invalid choice")
            else:
                if choice == "1":
                    self.store_file()
                elif choice == "2":
                    self.store_text()
                elif choice == "3":
                    self.retrieve_file()
                elif choice == "4":
                    self.list_files()
                elif choice == "5":
                    self.verify_integrity()
                elif choice == "6":
                    self.view_vault_status()
                elif choice == "7":
                    self.logout_user()
                elif choice == "0":
                    print("\n  Goodbye!")
                    break
                else:
                    print("  [ERROR] Invalid choice")


if __name__ == "__main__":
    app = SecureVaultApp()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n\n  Interrupted. Goodbye!")
        sys.exit(0)
