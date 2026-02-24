import os
import json
from src.seed_phrase import SeedPhrase
from src.vault_core_v2 import VaultCoreV2
from src.security import RateLimiter


class UserManagerV2:
    
    def __init__(self, users_dir: str = "vault_users"):
        self.users_dir = users_dir
        os.makedirs(users_dir, exist_ok=True)
        self.rate_limiter = RateLimiter(max_attempts=5, lockout_time=300)
    
    def register_user(self, username: str) -> tuple:
        user_path = os.path.join(self.users_dir, username)
        if os.path.exists(user_path):
            return False, "[ERROR] User already exists", None
        
        os.makedirs(user_path, exist_ok=True)
        
        seed_phrase = SeedPhrase.generate_phrase()
        password = SeedPhrase.phrase_to_password(seed_phrase)
        
        vault = VaultCoreV2(username, user_path)
        vault.initialize_vault(password)
        
        user_info = {
            "username": username,
            "created_at": __import__('datetime').datetime.utcnow().isoformat()
        }
        
        with open(os.path.join(user_path, "user_info.json"), 'w') as f:
            json.dump(user_info, f)
        
        return True, f"[OK] User '{username}' registered", seed_phrase
    
    def login_user(self, username: str, seed_phrase: list) -> tuple:
        user_path = os.path.join(self.users_dir, username)
        if not os.path.exists(user_path):
            self.rate_limiter.record_failure(username)
            return False, "[ERROR] User not found"
        
        if self.rate_limiter.is_locked(username):
            remaining = self.rate_limiter.get_remaining_lockout(username)
            return False, f"[ERROR] Account locked. Try again in {remaining}s"
        
        password = SeedPhrase.phrase_to_password(seed_phrase)
        
        vault = VaultCoreV2(username, user_path)
        
        try:
            if vault.unlock_vault(password):
                self.rate_limiter.record_success(username)
                return True, f"[OK] User '{username}' authenticated"
            else:
                self.rate_limiter.record_failure(username)
                return False, "[ERROR] Invalid seed phrase"
        except Exception:
            self.rate_limiter.record_failure(username)
            return False, "[ERROR] Authentication failed"
    
    def get_user_vault(self, username: str) -> VaultCoreV2:
        user_path = os.path.join(self.users_dir, username)
        return VaultCoreV2(username, user_path)
    
    def list_users(self) -> list:
        users = []
        for item in os.listdir(self.users_dir):
            user_path = os.path.join(self.users_dir, item)
            if os.path.isdir(user_path) and os.path.exists(os.path.join(user_path, "user_info.json")):
                users.append(item)
        return users
    
    def user_exists(self, username: str) -> bool:
        user_path = os.path.join(self.users_dir, username)
        return os.path.exists(user_path)
