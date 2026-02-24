import os
import secrets
from argon2.low_level import hash_secret, Type
from hkdf import hkdf_expand, hkdf_extract
from hashlib import sha256
from src.crypto_constants import (
    ARGON2_TIME_COST, ARGON2_MEMORY_COST, ARGON2_PARALLELISM,
    ARGON2_SALT_LENGTH, ARGON2_KEY_LENGTH,
    HKDF_INFO_ENCRYPTION, HKDF_INFO_METADATA, HKDF_INFO_SIGNING
)


class KeyDerivation:
    
    @staticmethod
    def generate_salt(length: int = ARGON2_SALT_LENGTH) -> bytes:
        return secrets.token_bytes(length)
    
    @staticmethod
    def derive_master_key(password: str, salt: bytes) -> bytes:
        password_bytes = password.encode('utf-8')
        
        hash_bytes = hash_secret(
            password_bytes,
            salt,
            time_cost=ARGON2_TIME_COST,
            memory_cost=ARGON2_MEMORY_COST,
            parallelism=ARGON2_PARALLELISM,
            hash_len=ARGON2_KEY_LENGTH,
            type=Type.ID
        )
        
        return hash_bytes[:ARGON2_KEY_LENGTH]
    
    @staticmethod
    def derive_keys(master_key: bytes) -> dict:
        salt = b""
        
        prk = hkdf_extract(salt, master_key, sha256)
        
        encryption_key = hkdf_expand(
            prk,
            HKDF_INFO_ENCRYPTION,
            length=32,
            hash=sha256
        )
        
        metadata_key = hkdf_expand(
            prk,
            HKDF_INFO_METADATA,
            length=32,
            hash=sha256
        )
        
        signing_key = hkdf_expand(
            prk,
            HKDF_INFO_SIGNING,
            length=32,
            hash=sha256
        )
        
        return {
            "encryption": encryption_key,
            "metadata": metadata_key,
            "signing": signing_key,
            "master": master_key
        }
    
    @staticmethod
    def clear_sensitive_data(data: bytes) -> None:
        if isinstance(data, bytearray):
            data[:] = bytes(len(data))
