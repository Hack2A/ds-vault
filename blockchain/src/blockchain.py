import time
from src.block import Block


class Blockchain:
    def __init__(self, difficulty: int = 3):
        self.difficulty = difficulty
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis = Block(index=0, data="Genesis Block", previous_hash="0" * 64)
        genesis.hash = genesis.compute_hash()
        self.chain.append(genesis)

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    @property
    def length(self) -> int:
        return len(self.chain)

    def proof_of_work(self, block: Block) -> str:
        target = "0" * self.difficulty
        block.nonce = 0
        computed_hash = block.compute_hash()
        
        while not computed_hash.startswith(target):
            block.nonce += 1
            computed_hash = block.compute_hash()
        
        return computed_hash

    def add_block(self, data) -> Block:
        new_block = Block(
            index=self.last_block.index + 1,
            data=data,
            previous_hash=self.last_block.hash
        )
        new_block.hash = self.proof_of_work(new_block)
        self.chain.append(new_block)
        return new_block

    def is_chain_valid(self) -> tuple:
        for block in self.chain[1:]:
            if block.previous_hash != self.chain[self.chain.index(block) - 1].hash:
                return False, "[INVALID] Hash mismatch - chain tampered"
            
            if not block.hash.startswith("0" * self.difficulty):
                return False, "[INVALID] Block hash doesn't match difficulty"
        
        return True, "[VALID] Chain is VALID - no tampering detected."
