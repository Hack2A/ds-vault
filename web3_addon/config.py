"""
web3/config.py — Feature flags and chain configuration for ds-vault Web3 layer.

All secrets are loaded from environment variables only.
Feature flags default to False — the vault works identically to the original
when USE_BLOCKCHAIN=False and USE_IPFS=False.

Supported chains:
    polygon_amoy       — Polygon Amoy Testnet  (DEFAULT)
    polygon_mainnet    — Polygon Mainnet
    ethereum_sepolia   — Ethereum Sepolia Testnet
    arbitrum_sepolia   — Arbitrum Sepolia Testnet
    base_sepolia       — Base Sepolia Testnet
    optimism_sepolia   — Optimism Sepolia Testnet

Usage:
    Set USE_BLOCKCHAIN=true in .env.web3 to enable on-chain verification.
    Set USE_IPFS=true to enable IPFS storage via Pinata.
"""

import os
from dotenv import load_dotenv

# Load from .env.web3 if present (project root), then fall back to .env
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_web3_env_path = os.path.join(_PROJECT_ROOT, ".env.web3")
if os.path.exists(_web3_env_path):
    load_dotenv(_web3_env_path, override=False)

# ─── Feature Flags ────────────────────────────────────────────────────────────

USE_BLOCKCHAIN: bool = os.getenv("USE_BLOCKCHAIN", "false").lower() == "true"
"""Master toggle. When False, all blockchain calls are skipped silently."""

USE_IPFS: bool = os.getenv("USE_IPFS", "false").lower() == "true"
"""IPFS toggle. When False, CID is stored as empty string."""

# ─── Active Chain ─────────────────────────────────────────────────────────────

ACTIVE_CHAIN: str = os.getenv("ACTIVE_CHAIN", "polygon_amoy")
"""
Which chain to use. Must be one of the keys in CHAIN_CONFIGS.
Defaults to polygon_amoy (most cost-effective testnet for verification).
"""

# ─── Chain Registry ───────────────────────────────────────────────────────────

CHAIN_CONFIGS: dict = {
    # ── Polygon ──────────────────────────────────────────────────────────────
    "polygon_amoy": {
        "name": "Polygon Amoy Testnet",
        "chain_id": 80002,
        "rpc_primary": os.getenv("POLYGON_AMOY_RPC", "https://rpc-amoy.polygon.technology"),
        "rpc_fallback": os.getenv("POLYGON_AMOY_RPC_FALLBACK", "https://polygon-amoy.drpc.org"),
        "explorer": "https://amoy.polygonscan.com",
        "contract_address": os.getenv("POLYGON_AMOY_CONTRACT_ADDRESS", ""),
    },
    "polygon_mainnet": {
        "name": "Polygon Mainnet",
        "chain_id": 137,
        "rpc_primary": os.getenv("POLYGON_RPC", "https://polygon-rpc.com"),
        "rpc_fallback": os.getenv("POLYGON_RPC_FALLBACK", "https://polygon.drpc.org"),
        "explorer": "https://polygonscan.com",
        "contract_address": os.getenv("POLYGON_CONTRACT_ADDRESS", ""),
    },
    # ── Ethereum ─────────────────────────────────────────────────────────────
    "ethereum_sepolia": {
        "name": "Ethereum Sepolia Testnet",
        "chain_id": 11155111,
        "rpc_primary": os.getenv("SEPOLIA_RPC", "https://rpc.sepolia.org"),
        "rpc_fallback": os.getenv("SEPOLIA_RPC_FALLBACK", "https://ethereum-sepolia.drpc.org"),
        "explorer": "https://sepolia.etherscan.io",
        "contract_address": os.getenv("SEPOLIA_CONTRACT_ADDRESS", ""),
    },
    # ── Arbitrum ─────────────────────────────────────────────────────────────
    "arbitrum_sepolia": {
        "name": "Arbitrum Sepolia Testnet",
        "chain_id": 421614,
        "rpc_primary": os.getenv(
            "ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc"
        ),
        "rpc_fallback": os.getenv(
            "ARBITRUM_SEPOLIA_RPC_FALLBACK", "https://arbitrum-sepolia.drpc.org"
        ),
        "explorer": "https://sepolia.arbiscan.io",
        "contract_address": os.getenv("ARBITRUM_SEPOLIA_CONTRACT_ADDRESS", ""),
    },
    # ── Base ─────────────────────────────────────────────────────────────────
    "base_sepolia": {
        "name": "Base Sepolia Testnet",
        "chain_id": 84532,
        "rpc_primary": os.getenv("BASE_SEPOLIA_RPC", "https://sepolia.base.org"),
        "rpc_fallback": os.getenv(
            "BASE_SEPOLIA_RPC_FALLBACK", "https://base-sepolia.drpc.org"
        ),
        "explorer": "https://sepolia.basescan.org",
        "contract_address": os.getenv("BASE_SEPOLIA_CONTRACT_ADDRESS", ""),
    },
    # ── Optimism ─────────────────────────────────────────────────────────────
    "optimism_sepolia": {
        "name": "Optimism Sepolia Testnet",
        "chain_id": 11155420,
        "rpc_primary": os.getenv("OPTIMISM_SEPOLIA_RPC", "https://sepolia.optimism.io"),
        "rpc_fallback": os.getenv(
            "OPTIMISM_SEPOLIA_RPC_FALLBACK", "https://optimism-sepolia.drpc.org"
        ),
        "explorer": "https://sepolia-optimism.etherscan.io",
        "contract_address": os.getenv("OPTIMISM_SEPOLIA_CONTRACT_ADDRESS", ""),
    },
}


def get_active_chain_config() -> dict:
    """Return the config dict for the currently active chain.

    Falls back to polygon_amoy if ACTIVE_CHAIN is unrecognised.
    """
    return CHAIN_CONFIGS.get(ACTIVE_CHAIN, CHAIN_CONFIGS["polygon_amoy"])


def list_chains() -> list[str]:
    """Return all supported chain keys."""
    return list(CHAIN_CONFIGS.keys())


# ─── Wallet Config (never hardcoded) ─────────────────────────────────────────

WALLET_ADDRESS: str = os.getenv("VAULT_WALLET_ADDRESS", "")
"""Ethereum-compatible wallet address (0x...)."""

PRIVATE_KEY: str = os.getenv("VAULT_PRIVATE_KEY", "")
"""
Private key for signing transactions.
NEVER commit this value. Load from environment or a secrets manager only.
"""

GAS_LIMIT: int = int(os.getenv("VAULT_GAS_LIMIT", "200000"))
"""Conservative gas limit for storeRecord transactions."""

# ─── IPFS / Pinata ────────────────────────────────────────────────────────────

PINATA_JWT: str = os.getenv("PINATA_JWT", "")
"""Pinata JWT token for authenticated uploads. Required for USE_IPFS=true."""

PINATA_GATEWAY: str = os.getenv(
    "PINATA_GATEWAY", "https://gateway.pinata.cloud"
)
"""Dedicated Pinata gateway for downloads (faster than public gateway)."""

IPFS_PUBLIC_GATEWAY: str = os.getenv(
    "IPFS_PUBLIC_GATEWAY", "https://ipfs.io"
)
"""Public IPFS gateway used as download fallback when Pinata is unavailable."""

IPFS_REQUEST_TIMEOUT: int = int(os.getenv("IPFS_REQUEST_TIMEOUT", "30"))
"""Timeout in seconds for IPFS upload/download requests."""
