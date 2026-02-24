from hashlib import sha256


class MerkleNode:
    def __init__(self, data: bytes = None, left=None, right=None):
        self.data = data
        self.left = left
        self.right = right
        self.hash = None
        
        if data is not None:
            self.hash = sha256(data).digest()
        elif left and right:
            combined = left.hash + right.hash
            self.hash = sha256(combined).digest()


class MerkleTree:
    
    def __init__(self, file_hashes: dict = None):
        self.file_hashes = file_hashes or {}
        self.root_hash = None
        self.tree = None
        self.file_to_node = {}
        
        if self.file_hashes:
            self._build_tree()
    
    def _build_tree(self):
        if not self.file_hashes:
            self.root_hash = sha256(b"empty").digest()
            return
        
        leaf_nodes = []
        for file_id, file_hash in sorted(self.file_hashes.items()):
            node = MerkleNode(data=file_hash)
            leaf_nodes.append(node)
            self.file_to_node[file_id] = node
        
        while len(leaf_nodes) > 1:
            if len(leaf_nodes) % 2 != 0:
                leaf_nodes.append(leaf_nodes[-1])
            
            parent_nodes = []
            for i in range(0, len(leaf_nodes), 2):
                left = leaf_nodes[i]
                right = leaf_nodes[i + 1]
                parent = MerkleNode(left=left, right=right)
                parent_nodes.append(parent)
            
            leaf_nodes = parent_nodes
        
        self.tree = leaf_nodes[0]
        self.root_hash = self.tree.hash
    
    def add_file(self, file_id: str, file_hash: bytes):
        self.file_hashes[file_id] = file_hash
        self._build_tree()
    
    def remove_file(self, file_id: str):
        if file_id in self.file_hashes:
            del self.file_hashes[file_id]
            self._build_tree()
    
    def update_file(self, file_id: str, file_hash: bytes):
        self.file_hashes[file_id] = file_hash
        self._build_tree()
    
    def get_root_hash(self) -> bytes:
        return self.root_hash
    
    def get_file_hash(self, file_id: str) -> bytes:
        return self.file_hashes.get(file_id)
    
    def serialize(self) -> dict:
        return {
            "file_hashes": {
                k: v.hex() for k, v in self.file_hashes.items()
            },
            "root_hash": self.root_hash.hex() if self.root_hash else None
        }
    
    @staticmethod
    def deserialize(data: dict):
        tree = MerkleTree()
        tree.file_hashes = {
            k: bytes.fromhex(v) for k, v in data["file_hashes"].items()
        }
        tree.root_hash = bytes.fromhex(data["root_hash"]) if data["root_hash"] else None
        tree._build_tree()
        return tree
