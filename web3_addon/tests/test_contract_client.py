"""
web3/tests/test_contract_client.py

Unit tests for contract_client.py using unittest.mock (no real RPC required).
These tests verify:
  - store_record returns None gracefully when wallet is unconfigured
  - store_record returns None gracefully when RPC is unreachable
  - store_record returns tx_hash on a successful mocked transaction
  - get_record returns None for unknown hashes
  - get_record returns the correct dict on a mocked response
  - All exceptions are swallowed (never raised to caller)
"""

import unittest
from unittest.mock import MagicMock, patch


# ─── A realistic 64-char hex SHA-256 hash ─────────────────────────────────────
VALID_HASH = "a" * 64  # 64 hex chars = 32 bytes
SHORT_HASH  = "ab"      # Too short — should be rejected
SAMPLE_TX   = "0x" + "1f" * 32  # Fake tx hash


class TestStoreRecord(unittest.TestCase):
    """Tests for web3.contract_client.store_record()"""

    def test_returns_none_when_wallet_not_configured(self):
        """Should silently return None if VAULT_PRIVATE_KEY or WALLET_ADDRESS is empty."""
        with patch("web3.contract_client._connect") as mock_connect, \
             patch("web3.config.PRIVATE_KEY", ""), \
             patch("web3.config.WALLET_ADDRESS", ""):
            from web3_addon.contract_client import store_record
            result = store_record(VALID_HASH, "")
            self.assertIsNone(result)
            mock_connect.assert_not_called()

    def test_returns_none_when_rpc_unreachable(self):
        """Should return None (not raise) when both RPCs are unreachable."""
        with patch("web3.contract_client._connect", return_value=(None, None)), \
             patch("web3.config.PRIVATE_KEY", "0x" + "aa" * 32), \
             patch("web3.config.WALLET_ADDRESS", "0x" + "bb" * 20):
            from web3_addon.contract_client import store_record
            result = store_record(VALID_HASH, "")
            self.assertIsNone(result)

    def test_returns_none_for_short_hash(self):
        """Should return None when hash is not 32 bytes (64 hex chars)."""
        with patch("web3.config.PRIVATE_KEY", "0x" + "aa" * 32), \
             patch("web3.config.WALLET_ADDRESS", "0x" + "bb" * 20):
            from web3_addon.contract_client import store_record
            result = store_record(SHORT_HASH, "")
            self.assertIsNone(result)

    def test_returns_none_for_invalid_hex(self):
        """Should return None when hash contains invalid hex characters."""
        with patch("web3.config.PRIVATE_KEY", "0x" + "aa" * 32), \
             patch("web3.config.WALLET_ADDRESS", "0x" + "bb" * 20):
            from web3_addon.contract_client import store_record
            result = store_record("zz" * 32, "")
            self.assertIsNone(result)

    def test_returns_tx_hash_on_success(self):
        """Should return tx hash string when transaction is submitted successfully."""
        mock_w3 = MagicMock()
        mock_contract = MagicMock()

        # Set up mock transaction submission
        mock_w3.eth.get_transaction_count.return_value = 1
        mock_w3.eth.gas_price = 30_000_000_000
        mock_contract.functions.storeRecord.return_value.build_transaction.return_value = {}

        mock_signed = MagicMock()
        mock_signed.raw_transaction = b"\x00" * 32
        mock_w3.eth.account.sign_transaction.return_value = mock_signed
        mock_w3.eth.send_raw_transaction.return_value = bytes.fromhex(SAMPLE_TX[2:])

        mock_cfg = {
            "name": "Test Chain",
            "chain_id": 31337,
            "contract_address": "0x" + "cc" * 20,
            "rpc_primary": "http://localhost:8545",
            "rpc_fallback": "http://localhost:8545",
        }

        with patch("web3.contract_client._connect", return_value=(mock_w3, mock_contract)), \
             patch("web3.config.PRIVATE_KEY", "0x" + "aa" * 32), \
             patch("web3.config.WALLET_ADDRESS", "0x" + "bb" * 20), \
             patch("web3.config.GAS_LIMIT", 200_000), \
             patch("web3.config.get_active_chain_config", return_value=mock_cfg):
            from web3 import Web3
            with patch("web3.contract_client.Web3.to_checksum_address", side_effect=lambda x: x):
                from web3_addon.contract_client import store_record
                result = store_record(VALID_HASH, "QmTestCID")
                # Result should be a hex string
                self.assertIsNotNone(result)
                self.assertIsInstance(result, str)

    def test_exception_is_swallowed(self):
        """Arbitrary exception inside store_record must NOT propagate to caller."""
        with patch("web3.contract_client._connect", side_effect=RuntimeError("network down")):
            from web3_addon.contract_client import store_record
            # Must not raise
            try:
                result = store_record(VALID_HASH, "")
                self.assertIsNone(result)
            except Exception as exc:
                self.fail(f"store_record raised an exception: {exc}")


class TestGetRecord(unittest.TestCase):
    """Tests for web3.contract_client.get_record()"""

    def test_returns_none_when_rpc_unreachable(self):
        """Should return None when _connect returns (None, None)."""
        with patch("web3.contract_client._connect", return_value=(None, None)):
            from web3_addon.contract_client import get_record
            result = get_record(VALID_HASH)
            self.assertIsNone(result)

    def test_returns_none_for_unregistered_hash(self):
        """Should return None when timestamp in record is 0 (record never stored)."""
        mock_w3 = MagicMock()
        mock_contract = MagicMock()
        # (fileHash bytes32, cid str, owner address, timestamp uint256)
        mock_contract.functions.getRecord.return_value.call.return_value = (
            bytes(32), "", "0x" + "00" * 20, 0
        )
        with patch("web3.contract_client._connect", return_value=(mock_w3, mock_contract)):
            from web3_addon.contract_client import get_record
            result = get_record(VALID_HASH)
            self.assertIsNone(result)

    def test_returns_dict_for_existing_record(self):
        """Should return a properly structured dict when record exists on-chain."""
        mock_w3 = MagicMock()
        mock_contract = MagicMock()

        file_hash_bytes = bytes.fromhex(VALID_HASH)
        mock_contract.functions.getRecord.return_value.call.return_value = (
            file_hash_bytes,
            "QmStoredCID",
            "0xDeAdBeEf" + "00" * 16,
            1_700_000_000,
        )
        with patch("web3.contract_client._connect", return_value=(mock_w3, mock_contract)):
            from web3_addon.contract_client import get_record
            result = get_record(VALID_HASH)

        self.assertIsNotNone(result)
        self.assertIn("cid", result)
        self.assertEqual(result["cid"], "QmStoredCID")
        self.assertEqual(result["timestamp"], 1_700_000_000)

    def test_exception_is_swallowed(self):
        """Arbitrary exception inside get_record must NOT propagate."""
        with patch("web3.contract_client._connect", side_effect=Exception("timeout")):
            from web3_addon.contract_client import get_record
            try:
                result = get_record(VALID_HASH)
                self.assertIsNone(result)
            except Exception as exc:
                self.fail(f"get_record raised an exception: {exc}")

    def test_returns_none_for_invalid_hex(self):
        """Should return None for a non-hex hash."""
        from web3_addon.contract_client import get_record
        result = get_record("not_a_hex_string")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
