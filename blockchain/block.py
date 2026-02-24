import hashlib
import json
import time


class Block:
    def __init__(self, index: int, data, previous_hash: str):
        self.index = index
        self.timestamp = time.time()
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        block_dict = {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
        }
        block_string = json.dumps(block_dict, sort_keys=True, default=str)
        return hashlib.sha256(block_string.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "hash": self.hash,
            "previous_hash": self.previous_hash,
            "data": self.data,
        }

    def __repr__(self) -> str:
        return f"Block(index={self.index}, hash={self.hash[:12]}..., nonce={self.nonce})"
