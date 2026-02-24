import time
import json
import os
from pathlib import Path


class RateLimiter:
    
    def __init__(self, max_attempts: int = 5, lockout_time: int = 300):
        self.max_attempts = max_attempts
        self.lockout_time = lockout_time
        self.attempts = {}
        self.locked_until = {}
    
    def record_failure(self, identifier: str):
        current_time = time.time()
        
        if identifier in self.locked_until:
            if current_time < self.locked_until[identifier]:
                raise PermissionError(f"Account locked until {self.locked_until[identifier]}")
        
        if identifier not in self.attempts:
            self.attempts[identifier] = []
        
        self.attempts[identifier] = [t for t in self.attempts[identifier] if current_time - t < self.lockout_time]
        self.attempts[identifier].append(current_time)
        
        if len(self.attempts[identifier]) >= self.max_attempts:
            self.locked_until[identifier] = current_time + self.lockout_time
            raise PermissionError(f"Too many failed attempts. Locked for {self.lockout_time} seconds.")
    
    def record_success(self, identifier: str):
        if identifier in self.attempts:
            self.attempts[identifier] = []
        if identifier in self.locked_until:
            del self.locked_until[identifier]
    
    def is_locked(self, identifier: str) -> bool:
        current_time = time.time()
        
        if identifier in self.locked_until:
            if current_time < self.locked_until[identifier]:
                return True
            else:
                del self.locked_until[identifier]
        
        return False
    
    def get_remaining_lockout(self, identifier: str) -> int:
        current_time = time.time()
        
        if identifier in self.locked_until:
            remaining = self.locked_until[identifier] - current_time
            return max(0, int(remaining))
        
        return 0


class TamperingDetection:
    
    @staticmethod
    def check_vault_integrity(merkle_root: bytes, signature: bytes, public_key) -> bool:
        from blockchain.signing import DigitalSignature
        return DigitalSignature.verify_signature(merkle_root, signature, public_key)
    
    @staticmethod
    def create_integrity_check(merkle_root: bytes, private_key) -> bytes:
        from blockchain.signing import DigitalSignature
        return DigitalSignature.sign_data(merkle_root, private_key)
    
    @staticmethod
    def verify_file_tampering(original_hash: bytes, current_hash: bytes) -> bool:
        from Encryption.encryption import ConstantTimeComparison
        return ConstantTimeComparison.compare_bytes(original_hash, current_hash)


class SecureMemory:
    
    @staticmethod
    def clear_bytes(data: bytes) -> None:
        if isinstance(data, bytearray):
            data[:] = bytes(len(data))
    
    @staticmethod
    def create_mutable_copy(data: bytes) -> bytearray:
        return bytearray(data)
    
    @staticmethod
    def secure_delete_file(file_path: str, passes: int = 3):
        if not os.path.exists(file_path):
            return
        
        file_size = os.path.getsize(file_path)
        
        for _ in range(passes):
            with open(file_path, 'wb') as f:
                f.write(os.urandom(file_size))
        
        os.remove(file_path)
