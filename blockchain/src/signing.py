import secrets
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


class DigitalSignature:
    
    @staticmethod
    def generate_keypair() -> tuple:
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key
    
    @staticmethod
    def sign_data(data: bytes, private_key) -> bytes:
        signature = private_key.sign(data)
        return signature
    
    @staticmethod
    def verify_signature(data: bytes, signature: bytes, public_key) -> bool:
        try:
            public_key.verify(signature, data)
            return True
        except Exception:
            return False
    
    @staticmethod
    def serialize_private_key(private_key) -> bytes:
        return private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
    
    @staticmethod
    def serialize_public_key(public_key) -> bytes:
        return public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
    
    @staticmethod
    def deserialize_private_key(key_bytes: bytes):
        return ed25519.Ed25519PrivateKey.from_private_bytes(key_bytes)
    
    @staticmethod
    def deserialize_public_key(key_bytes: bytes):
        return ed25519.Ed25519PublicKey.from_public_bytes(key_bytes)
