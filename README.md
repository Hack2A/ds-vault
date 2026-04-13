# ds-vault

> **AES-GCM encrypted, Ethereum-verified, zero-knowledge personal vault.**

**ds-vault** is a secure, full-stack secret management system with a live blockchain integrity layer. Secrets are encrypted at rest using AES-256-GCM with Argon2id key derivation and a 12-word BIP-39 seed phrase. A SHA-256 fingerprint of every secret is permanently logged on the **Ethereum Sepolia blockchain** — giving anyone with the hash cryptographic proof that the secret was never tampered with.

The blockchain layer is completely opt-in. The vault works identically without it.

---

## Features

- **AES-256-GCM encryption** — authenticated encryption for all stored data
- **Argon2id key derivation** — memory-hard, GPU-resistant password hashing
- **12-word BIP-39 seed phrase** — your master key, generated locally, never transmitted
- **Local Proof-of-Work blockchain** — tamper-evident linked chain for every stored item
- **Ethereum on-chain verification** — SHA-256 hash of every secret logged on Sepolia permanently
- **Etherscan-ready** — every stored item generates a clickable Etherscan verification link in the CLI
- **Zero-knowledge design** — only hashes go on-chain, plaintext never leaves your machine
- **Web API bridge** — stateless `VaultAPI` class ready to plug into Django/FastAPI
- **Full-stack web app** — Next.js frontend + Django REST backend + JWT/OAuth auth

---

## Architecture

```
ds-vault/
├── Encryption/              # Core vault logic
│   ├── secure_vault.py      # Interactive CLI entrypoint
│   ├── vault_core.py        # Storage, encryption + local blockchain engine
│   ├── vault_api.py         # Stateless API bridge (Django/FastAPI integration)
│   ├── encryption.py        # AES-GCM primitives
│   ├── key_derivation.py    # Argon2id key derivation
│   ├── user_manager.py      # User registration / seed-phrase authentication
│   └── seed_phrase.py       # BIP-39 mnemonic generation
│
├── blockchain/              # Local proof-of-work chain
│   └── blockchain.py        # Block, Blockchain classes
│
├── contracts/               # Ethereum smart contract
│   ├── contracts/
│   │   └── VaultRegistry.sol   # On-chain hash registry (deployed on Sepolia)
│   ├── scripts/deploy.js    # Multi-chain deployment script
│   ├── test/                # Hardhat test suite (15 tests, all passing)
│   └── hardhat.config.js    # Network config (Sepolia, Polygon, Base, Arbitrum...)
│
├── web3_addon/              # Ethereum integration layer (optional)
│   ├── config.py            # Feature flags, chain registry, RPC endpoints
│   ├── contract_client.py   # Web3.py wrapper for VaultRegistry
│   └── ipfs_client.py       # Pinata IPFS pinning client
│
├── server/                  # Django REST backend
│   ├── api/                 # Vault API endpoints
│   └── requirements.txt     # Python dependencies
│
├── client/                  # Next.js frontend
│   └── src/                 # React components + pages
│
├── .env.web3                # Blockchain config (git-ignored — never commit!)
└── .env.web3.example        # Config template (safe to commit)
```

---

## How It Works

### Storing a Secret (Advanced Mode)

```
User types secret text
        │
        ▼
[AES-256-GCM]  ←  key derived from seed phrase via Argon2id + random 16-byte salt
        │
        ▼
Ciphertext saved to vault_users/<user>/files/<item>.enc  (local disk only)
        │
        ▼
[SHA-256 Hash]  of the original plaintext
        │
        ├──► [Local PoW Chain]    Block mined + chained  →  Block #N
        │
        └──► [Ethereum Sepolia]   Hash sent to VaultRegistry.sol
                                  → Transaction Hash printed + stored in metadata
                                  → Etherscan verification link generated instantly
```

### Verifying / Retrieving a Secret

```
User requests item
        │
        ▼
Ciphertext loaded from local disk
        │
        ▼
[AES-256-GCM Decrypt]  ←  key re-derived from seed phrase + stored salt
        │
        ▼
[SHA-256]  of decrypted plaintext
        │
        ├──► Compare with local blockchain block record
        │
        └──► if USE_BLOCKCHAIN=true:
               Query VaultRegistry.sol on Ethereum Sepolia
               Compare on-chain hash vs. computed hash
               ✅ Match → tamper-free  |  ❌ Mismatch → ALERT
```

---

## Live Deployment

| Property | Value |
|----------|-------|
| **Contract Network** | Ethereum Sepolia Testnet |
| **Contract Address** | `0xaF1521e67Dc97cbC0F4763bfb6D2B6483EFD67f9` |
| **Etherscan** | [View Contract](https://sepolia.etherscan.io/address/0xaF1521e67Dc97cbC0F4763bfb6D2B6483EFD67f9) |

---

## Quick Start (CLI Vault)

### 1. Set up Python environment

```bash
git clone https://github.com/Hack2A/ds-vault
cd ds-vault

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install web3 python-dotenv requests argon2-cffi
```

### 2. Configure blockchain settings

```bash
cp .env.web3.example .env.web3
```

Edit `.env.web3`:
```env
USE_BLOCKCHAIN=true
ACTIVE_CHAIN=ethereum_sepolia
VAULT_WALLET_ADDRESS=0xYourWalletAddress
VAULT_PRIVATE_KEY=0xYourPrivateKey
SEPOLIA_CONTRACT_ADDRESS=0xaF1521e67Dc97cbC0F4763bfb6D2B6483EFD67f9
```

> ⚠️ Never commit `.env.web3`. Use a dedicated testnet wallet — never your main wallet.

### 3. Run the vault

```bash
python Encryption/secure_vault.py
```

| Option | Action |
|--------|--------|
| `1` (outer menu) | Register a new user + generate seed phrase |
| `2` (outer menu) | Login with your 12-word seed phrase |
| `2` (inner menu) | Store text — pick **Advanced Mode** for blockchain logging |
| `3` | Retrieve and decrypt a stored item |
| `5` | Verify integrity — prints live Etherscan link |

---

## Full Stack Setup (web app)

### Docker (Recommended)

```bash
docker compose up --build
```

- Frontend → `http://localhost:3000`
- Backend API → `http://localhost:8000`

### Manual Setup

**Backend:**
```bash
cd server
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**Frontend:**
```bash
cd client
npm install
npm run dev
```

---

## Smart Contract

### Deploy to a different network

```bash
cd contracts
npm install

npm run deploy:sepolia    # Ethereum Sepolia ← currently deployed
npm run deploy:amoy       # Polygon Amoy
npm run deploy:base       # Base Sepolia
npm run deploy:polygon    # Polygon Mainnet (production)
```

### Run smart contract tests

```bash
cd contracts
npm test
# 15 tests passing ✓
```

---

## Deploy Backend to Render

**1. Create a Web Service** — choose **Docker**, set Dockerfile path to `server/Dockerfile`, build context to `.`.

**2. Add PostgreSQL** — New → PostgreSQL, copy the Internal Database URL.

**3. Set Environment Variables:**

| Variable | Value |
|----------|-------|
| `SECRET_KEY` | Long random string |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `your-service.onrender.com` |
| `DATABASE_URL` | From your Render Postgres instance |
| `CORS_ALLOWED_ORIGINS` | Your frontend URL |
| `EMAIL_HOST_USER` | Gmail address |
| `EMAIL_HOST_PASSWORD` | Gmail App Password |

See `.env.render.example` for the full variable reference.

**4. Click Deploy.** Render will build the image, run migrations, and serve the API on port 8000.

---

## Security Design

| Property | Implementation |
|----------|---------------|
| Encryption | AES-256-GCM (authenticated, tamper-proof) |
| Key derivation | Argon2id (memory-hard, GPU-resistant) |
| Authentication | 12-word BIP-39 seed phrase |
| Integrity | SHA-256 + local PoW chain + Ethereum on-chain record |
| Zero-knowledge | Only hash goes on-chain, never plaintext |
| Key isolation | Private key lives only in `.env.web3`, never in code |
| Graceful fallback | Blockchain errors never crash the vault |

---

## License

MIT © ds-vault contributors
