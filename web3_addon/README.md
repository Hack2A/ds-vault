# ds-vault

> **AES-GCM encrypted, Ethereum-verified, zero-knowledge personal vault.**

A secure, local-first secret management system with an optional decentralized blockchain integrity layer. Secrets are encrypted at rest using AES-256-GCM with Argon2id key derivation. A SHA-256 fingerprint of each secret is permanently logged on the Ethereum blockchain — so anyone (with your hash) can cryptographically prove your file has never been tampered with.

Blockchain is opt-in. The vault works identically with `USE_BLOCKCHAIN=false`.

---

## Key Features

- **AES-256-GCM encryption** — military-grade authenticated encryption for all stored items
- **Argon2id key derivation** — memory-hard password hashing resistant to brute-force
- **12-word BIP-39 seed phrase** — your master key, generated locally, never transmitted
- **Local PoW blockchain** — tamper-evident linked chain of blocks for every stored item
- **Ethereum Sepolia verification** — SHA-256 hash of every secret logged on the public blockchain
- **Zero-knowledge design** — plaintext never leaves your machine
- **Graceful degradation** — blockchain failures fall back silently; the vault always works

---

## Architecture

```
ds-vault/
├── Encryption/              # Core vault logic
│   ├── secure_vault.py      # Interactive CLI entrypoint
│   ├── vault_core.py        # Storage, encryption, local blockchain engine
│   ├── vault_api.py         # Stateless API layer (Django/web integration bridge)
│   ├── vault_storage.py     # Encrypted file persistence
│   ├── encryption.py        # AES-GCM primitives (FileEncryption, AESGCMEncryption)
│   ├── key_derivation.py    # Argon2id key derivation
│   ├── user_manager.py      # User registration/authentication via seed phrase
│   ├── seed_phrase.py       # BIP-39 mnemonic generation
│   └── security.py         # Input validation and security utilities
│
├── blockchain/              # Local proof-of-work chain
│   └── blockchain.py        # Block, Blockchain classes
│
├── contracts/               # Ethereum smart contract
│   ├── contracts/
│   │   └── VaultRegistry.sol  # On-chain hash registry
│   ├── scripts/deploy.js    # Multi-chain deployment script
│   ├── test/                # Hardhat test suite (15 tests, all passing)
│   └── hardhat.config.js    # Network config (Sepolia, Polygon, Base, Arbitrum...)
│
├── web3_addon/              # Ethereum integration (optional layer)
│   ├── config.py            # Feature flags, chain registry, RPC endpoints
│   ├── contract_client.py   # Web3.py wrapper for VaultRegistry.storeRecord()
│   └── ipfs_client.py       # Pinata IPFS pinning client
│
├── server/                  # Django REST backend (API server)
├── client/                  # Frontend application
├── .env.web3                # Secret config (git-ignored — never commit!)
└── .env.web3.example        # Config template (safe to commit)
```

---

## How It Works

### Storing a Secret (Advanced Mode)

```
User types secret text
        │
        ▼
[AES-256-GCM]  ← key derived from seed phrase via Argon2id + random salt
        │
        ▼
Ciphertext saved to vault_users/<user>/files/<item>.enc  (local disk)
        │
        ▼
[SHA-256 Hash]  of the original plaintext
        │
        ├──► [Local PoW Blockchain]  Block mined + chained (tamper-evident ledger)
        │
        └──► [Ethereum Sepolia]  Hash submitted to VaultRegistry.sol smart contract
                                 Transaction Hash returned and stored in metadata
```

### Verifying / Retrieving a Secret

```
User requests retrieval
        │
        ▼
Ciphertext loaded from disk
        │
        ▼
[AES-256-GCM decrypt]  ← key re-derived from seed phrase + stored salt
        │
        ▼
[SHA-256 Hash]  of the freshly decrypted plaintext
        │
        ├──► Compare against local blockchain block record
        │
        └──► if USE_BLOCKCHAIN=true:
               Query VaultRegistry.sol on Ethereum
               Compare on-chain hash with computed hash
               ✅ Match → tamper-free  |  ❌ Mismatch → ALERT
```

---

## Deployed Contract

| Property | Value |
|----------|-------|
| **Network** | Ethereum Sepolia Testnet |
| **Contract Address** | `0xaF1521e67Dc97cbC0F4763bfb6D2B6483EFD67f9` |
| **Explorer** | [View on Etherscan](https://sepolia.etherscan.io/address/0xaF1521e67Dc97cbC0F4763bfb6D2B6483EFD67f9) |
| **Deployer Wallet** | `0x1a3C5e904a3894355761A2579806e949CF050519` |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- A funded Ethereum testnet wallet

### 1. Clone and set up Python environment

```bash
git clone https://github.com/yourname/ds-vault
cd ds-vault

python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux

pip install web3 python-dotenv requests argon2-cffi pytest
```

### 2. Configure your environment

```bash
cp .env.web3.example .env.web3
```

Edit `.env.web3` and fill in at minimum:
```env
USE_BLOCKCHAIN=true
ACTIVE_CHAIN=ethereum_sepolia

VAULT_WALLET_ADDRESS=0xYourWalletAddress
VAULT_PRIVATE_KEY=0xYourPrivateKey

SEPOLIA_CONTRACT_ADDRESS=0xaF1521e67Dc97cbC0F4763bfb6D2B6483EFD67f9
```

> ⚠️ **Warning:** Never commit `.env.web3`. It is already in `.gitignore`. Use a **dedicated vault wallet** with testnet funds only — never your main wallet.

### 3. Run the vault CLI

```bash
python Encryption/secure_vault.py
```

Choose:
- **Option 1** → Register a new user (generates your 12-word seed phrase)
- **Option 2** → Login with your seed phrase
- **Option 2 (inner)** → Store text in Advanced Mode (AES-GCM + Blockchain)
- **Option 5** → Verify integrity + get Etherscan link for any stored item

---

## Smart Contract

### Deploy to a new network

```bash
cd contracts
npm install

npm run deploy:sepolia    # Ethereum Sepolia (recommended for testing)
npm run deploy:amoy       # Polygon Amoy
npm run deploy:base       # Base Sepolia
npm run deploy:polygon    # Polygon Mainnet (production)
```

Copy the printed contract address to your `.env.web3`:
```env
SEPOLIA_CONTRACT_ADDRESS=0xYourDeployedContractAddress
```

### Run the smart contract test suite

```bash
cd contracts
npm test
# 15 passing ✓
```

### VaultRegistry.sol interface

```solidity
// Store a hash + optional IPFS CID on-chain
function storeRecord(bytes32 fileHash, string memory cid) external

// Check if a hash exists on-chain
function exists(bytes32 fileHash) external view returns (bool)

// Get full record: CID, owner address, timestamp
function getRecord(bytes32 fileHash) external view returns (string, address, uint256)
```

---

## Supported Chains

| Key | Network | Chain ID | Status |
|-----|---------|----------|--------|
| `ethereum_sepolia` | Ethereum Sepolia | 11155111 | ✅ **Active (deployed)** |
| `polygon_amoy` | Polygon Amoy Testnet | 80002 | Ready to deploy |
| `polygon_mainnet` | Polygon Mainnet | 137 | Production |
| `arbitrum_sepolia` | Arbitrum Sepolia | 421614 | Ready to deploy |
| `base_sepolia` | Base Sepolia | 84532 | Ready to deploy |
| `optimism_sepolia` | Optimism Sepolia | 11155420 | Ready to deploy |

---

## Web / Django Integration

`Encryption/vault_api.py` is a stateless API bridge designed for web backend integration. Drop it into any Django or FastAPI project:

```python
from Encryption.vault_api import VaultAPI

api = VaultAPI()

# Encrypt and store on-chain
result = api.encrypt(
    username="alice",
    item_name="api_key",
    plaintext="sk-super-secret-key",
    advanced=True,
    seed_phrase="your twelve word seed phrase here"
)
# result = {"success": True, "ciphertext": "a1b2c3...", "block_hash": "0x..."}

# Decrypt with chain verification
result = api.decrypt(
    username="alice",
    item_name="api_key",
    ciphertext_hex=result["ciphertext"],
    advanced=True,
    seed_phrase="your twelve word seed phrase here",
    block_hash=result["block_hash"]
)
# result = {"success": True, "plaintext": "sk-super-secret-key"}
```

---

## Configuration Reference (`.env.web3`)

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_BLOCKCHAIN` | `false` | Enable Ethereum on-chain hash registration |
| `USE_IPFS` | `false` | Enable IPFS pinning via Pinata |
| `ACTIVE_CHAIN` | `polygon_amoy` | Which network to write to |
| `VAULT_WALLET_ADDRESS` | — | Your deployer/signer wallet address |
| `VAULT_PRIVATE_KEY` | — | Private key for signing transactions |
| `VAULT_GAS_LIMIT` | `200000` | Max gas units per transaction |
| `SEPOLIA_CONTRACT_ADDRESS` | — | Deployed VaultRegistry address on Sepolia |
| `PINATA_JWT` | — | Pinata JWT (only needed if `USE_IPFS=true`) |

---

## Vault Metadata Structure

Each stored item writes to `vault_users/<user>/_vault_metadata.json`:

```json
{
  "my_secret": {
    "original_hash": "sha256-hex-of-plaintext",
    "salt": "hex-random-salt",
    "nonce": "hex-aes-nonce",
    "raw_key": null,
    "file_size": 42,
    "encrypted_size": 58,
    "stored_at": "2026-04-13T19:52:00",
    "block_number": 1,
    "is_text": true,
    "mode": "advanced",
    "tx_hash": "ethereum-transaction-hash",
    "cid": ""
  }
}
```

---

## Security Design

| Property | Implementation |
|----------|---------------|
| **Encryption** | AES-256-GCM (authenticated encryption, tamper-proof) |
| **Key derivation** | Argon2id (memory-hard, GPU-resistant) |
| **Authentication** | 12-word BIP-39 seed phrase (2048^12 combinations) |
| **Integrity** | SHA-256 hash + local PoW chain + Ethereum on-chain record |
| **Zero-knowledge** | Only hash goes on-chain, never plaintext |
| **Key isolation** | Private key lives only in `.env.web3`, never in code |
| **Graceful fallback** | Blockchain errors never crash the vault |

---

## License

MIT © ds-vault contributors
