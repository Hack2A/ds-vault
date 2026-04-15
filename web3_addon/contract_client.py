"""
web3/contract_client.py — EVM blockchain client for ds-vault.

Provides two public functions:
    store_record(file_hash_hex, cid) -> tx_hash | None
    get_record(file_hash_hex) -> dict | None

Design principles:
  - All network/RPC failures are caught and logged; functions return None.
  - Blockchain errors NEVER propagate into vault encrypt/decrypt logic.
  - Dual RPC fallback: primary → secondary → None (graceful degradation).
  - No secrets are stored; private key is loaded from environment config only.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Minimal ABI — only the two functions and one event we interact with.
_VAULT_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "fileHash", "type": "bytes32"},
            {"internalType": "string", "name": "cid", "type": "string"},
        ],
        "name": "storeRecord",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "fileHash", "type": "bytes32"},
        ],
        "name": "getRecord",
        "outputs": [
            {
                "components": [
                    {"internalType": "bytes32", "name": "fileHash", "type": "bytes32"},
                    {"internalType": "string", "name": "cid", "type": "string"},
                    {"internalType": "address", "name": "owner", "type": "address"},
                    {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
                ],
                "internalType": "struct VaultRegistry.Record",
                "name": "",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "fileHash", "type": "bytes32"},
        ],
        "name": "exists",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "fileHash", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "owner", "type": "address"},
            {"indexed": False, "internalType": "string", "name": "cid", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"},
        ],
        "name": "RecordStored",
        "type": "event",
    },
]


def _build_web3(rpc_url: str):
    """Attempt to connect to an RPC endpoint.

    Parameters
    ----------
    rpc_url : str
        HTTP(S) RPC endpoint URL.

    Returns
    -------
    Web3 | None
        Connected Web3 instance or None if the endpoint is unreachable.
    """
    try:
        from web3 import Web3

        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 10}))
        if w3.is_connected():
            return w3
        logger.warning("RPC endpoint not reachable: %s", rpc_url)
        return None
    except Exception as exc:
        logger.warning("Web3 connection error (%s): %s", rpc_url, exc)
        return None


def _connect():
    """Build a Web3 + contract pair using the active chain config.

    Tries primary RPC, falls back to secondary RPC.

    Returns
    -------
    (Web3, Contract) | (None, None)
        Connected pair or (None, None) on any failure.
    """
    try:
        from web3 import Web3
        from web3_addon.config import get_active_chain_config

        cfg = get_active_chain_config()
        contract_address = cfg.get("contract_address", "").strip()

        if not contract_address:
            logger.info(
                "No contract address configured for chain '%s' — blockchain disabled.",
                cfg["name"],
            )
            return None, None

        # Primary RPC → fallback RPC
        w3 = _build_web3(cfg["rpc_primary"])
        if w3 is None:
            logger.warning(
                "Primary RPC failed for %s, trying fallback...", cfg["name"]
            )
            w3 = _build_web3(cfg["rpc_fallback"])

        if w3 is None:
            logger.error(
                "Both primary and fallback RPCs are unreachable for %s.", cfg["name"]
            )
            return None, None

        checksum_addr = Web3.to_checksum_address(contract_address)
        contract = w3.eth.contract(address=checksum_addr, abi=_VAULT_ABI)
        return w3, contract

    except Exception as exc:
        logger.error("_connect() failed: %s", exc)
        return None, None


def store_record(file_hash_hex: str, cid: str = "") -> Optional[str]:
    """Submit a file hash + optional IPFS CID to the on-chain registry.

    This is a fire-and-return operation: the transaction is submitted and the
    hash is returned immediately without waiting for on-chain confirmation.
    This keeps vault encryption responsive even on slow networks.

    Parameters
    ----------
    file_hash_hex : str
        SHA-256 hex digest of the plaintext (64 hex characters = 32 bytes).
    cid : str, optional
        IPFS Content Identifier. Pass empty string when IPFS is disabled.

    Returns
    -------
    str | None
        Transaction hash (0x...) on success, None on any failure.
    """
    try:
        from web3 import Web3
        from web3_addon.config import PRIVATE_KEY, WALLET_ADDRESS, GAS_LIMIT, get_active_chain_config

        # Guard: wallet must be configured
        if not PRIVATE_KEY or not WALLET_ADDRESS:
            logger.warning(
                "Wallet not configured (VAULT_WALLET_ADDRESS / VAULT_PRIVATE_KEY) "
                "— skipping on-chain record."
            )
            return None

        # Validate hash length (must be 32 bytes = 64 hex chars)
        try:
            file_hash_bytes32 = bytes.fromhex(file_hash_hex)
        except ValueError:
            logger.error("store_record: invalid file_hash_hex (not valid hex).")
            return None

        if len(file_hash_bytes32) != 32:
            logger.error(
                "store_record: file_hash_hex must be 64 hex chars (32 bytes), got %d bytes.",
                len(file_hash_bytes32),
            )
            return None

        w3, contract = _connect()
        if w3 is None:
            return None

        cfg = get_active_chain_config()
        wallet_checksum = Web3.to_checksum_address(WALLET_ADDRESS)
        nonce = w3.eth.get_transaction_count(wallet_checksum)
        gas_price = w3.eth.gas_price

        txn = contract.functions.storeRecord(file_hash_bytes32, cid).build_transaction(
            {
                "chainId": cfg["chain_id"],
                "gas": GAS_LIMIT,
                "gasPrice": gas_price,
                "nonce": nonce,
                "from": wallet_checksum,
            }
        )

        signed = w3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
        raw_tx = signed.raw_transaction if hasattr(signed, "raw_transaction") else signed.rawTransaction
        tx_hash_bytes = w3.eth.send_raw_transaction(raw_tx)
        tx_hash_hex = tx_hash_bytes.hex()

        logger.info(
            "On-chain record submitted — chain: %s, tx: %s",
            cfg["name"],
            tx_hash_hex,
        )
        return tx_hash_hex

    except Exception as exc:
        # Non-blocking: log and return None so vault can continue locally
        logger.error("store_record failed (non-blocking fallback to local): %s", exc)
        return None


def get_record(file_hash_hex: str) -> Optional[dict]:
    """Fetch the on-chain record for a file hash.

    Parameters
    ----------
    file_hash_hex : str
        SHA-256 hex digest of the plaintext (64 hex characters).

    Returns
    -------
    dict | None
        {"file_hash", "cid", "owner", "timestamp"} on success,
        None if the record is not found or any error occurs.
    """
    try:
        try:
            file_hash_bytes32 = bytes.fromhex(file_hash_hex)
        except ValueError:
            logger.error("get_record: invalid file_hash_hex.")
            return None

        if len(file_hash_bytes32) != 32:
            return None

        w3, contract = _connect()
        if w3 is None:
            return None

        # (fileHash bytes32, cid str, owner address, timestamp uint256)
        record = contract.functions.getRecord(file_hash_bytes32).call()

        # timestamp == 0 → record never stored
        if record[3] == 0:
            logger.info("No on-chain record found for hash %s...", file_hash_hex[:16])
            return None

        return {
            "file_hash": record[0].hex(),
            "cid": record[1],
            "owner": record[2],
            "timestamp": record[3],
        }

    except Exception as exc:
        logger.error("get_record failed (non-blocking): %s", exc)
        return None


def get_chain_info() -> dict:
    """Return the currently active chain configuration (for diagnostics).

    Returns
    -------
    dict
        Chain name, chain_id, explorer URL, and whether a contract is configured.
    """
    try:
        from web3_addon.config import get_active_chain_config, ACTIVE_CHAIN

        cfg = get_active_chain_config()
        return {
            "active_chain": ACTIVE_CHAIN,
            "name": cfg["name"],
            "chain_id": cfg["chain_id"],
            "explorer": cfg["explorer"],
            "contract_configured": bool(cfg.get("contract_address", "").strip()),
        }
    except Exception as exc:
        logger.error("get_chain_info failed: %s", exc)
        return {}
