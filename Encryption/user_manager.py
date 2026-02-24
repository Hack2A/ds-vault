import json
import os
from Encryption.seed_phrase import SeedPhraseAuth
from Encryption.encryption import FileEncryption


class UserManager:
    def __init__(self, users_dir: str = "vault_users"):
        self.users_dir = users_dir
        self.users_file = os.path.join(users_dir, "users.json")
        self.users_db = {}
        
        os.makedirs(users_dir, exist_ok=True)
        self._load_users()

    def _load_users(self):
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    self.users_db = json.load(f)
            except Exception:
                pass

    def _save_users(self):
        with open(self.users_file, 'w') as f:
            json.dump(self.users_db, f, indent=2)

    def register_user(self, username: str):
        if username in self.users_db:
            return False, f"User '{username}' already exists", None
        
        auth = SeedPhraseAuth()
        seed_phrase = auth.generate_phrase()
        auth.register(username, seed_phrase)
        
        self.users_db[username] = {
            "seed_hash": auth.stored_hash,
            "vault_dir": os.path.join(self.users_dir, username),
            "files_count": 0,
            "total_size": 0,
            "created_at": str(__import__('datetime').datetime.now())
        }
        
        vault_dir = self.users_db[username]["vault_dir"]
        os.makedirs(os.path.join(vault_dir, "files"), exist_ok=True)
        
        self._save_users()
        return True, f"User '{username}' registered", seed_phrase

    def login_user(self, username: str, seed_phrase: list):
        if username not in self.users_db:
            return False, f"User '{username}' not found"
        
        auth = SeedPhraseAuth()
        auth.user_id = username
        auth.stored_hash = self.users_db[username]["seed_hash"]
        
        success, msg = auth.verify(username, seed_phrase)
        return success, msg

    def get_user_vault_dir(self, username: str) -> str:
        if username in self.users_db:
            return self.users_db[username]["vault_dir"]
        return None

    def list_users(self) -> list:
        return list(self.users_db.keys())

    def get_user_info(self, username: str) -> dict:
        if username in self.users_db:
            return self.users_db[username]
        return {}

    def update_user_stats(self, username: str, files_count: int = None, total_size: int = None):
        if username in self.users_db:
            if files_count is not None:
                self.users_db[username]["files_count"] = files_count
            if total_size is not None:
                self.users_db[username]["total_size"] = total_size
            self._save_users()
