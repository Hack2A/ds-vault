"""
web3/tests/test_ipfs_client.py

Unit tests for ipfs_client.py using unittest.mock (no real network calls).
Tests verify:
  - upload_to_ipfs returns None when PINATA_JWT is not set
  - upload_to_ipfs returns CID on a mocked successful Pinata response
  - upload_to_ipfs returns None on HTTP errors
  - download_from_ipfs returns None for empty CID
  - download_from_ipfs tries Pinata gateway first, falls back to public
  - download_from_ipfs returns None when all gateways fail
  - All exceptions are swallowed (never raised to caller)
"""

import unittest
from unittest.mock import patch, MagicMock


class TestUploadToIPFS(unittest.TestCase):
    """Tests for web3.ipfs_client.upload_to_ipfs()"""

    def test_returns_none_when_jwt_not_set(self):
        """Should skip upload and return None when PINATA_JWT is empty."""
        with patch("web3.config.PINATA_JWT", ""):
            from web3_addon.ipfs_client import upload_to_ipfs
            result = upload_to_ipfs(b"test data", "test.txt")
            self.assertIsNone(result)

    def test_returns_cid_on_success(self):
        """Should return the CID from Pinata on a successful 200 response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"IpfsHash": "QmTestCID123abc"}
        mock_response.raise_for_status = MagicMock()

        with patch("web3.config.PINATA_JWT", "fake_jwt_token"), \
             patch("web3.config.IPFS_REQUEST_TIMEOUT", 30), \
             patch("requests.post", return_value=mock_response):
            from web3_addon.ipfs_client import upload_to_ipfs
            result = upload_to_ipfs(b"encrypted vault data", "vault.enc")

        self.assertEqual(result, "QmTestCID123abc")

    def test_returns_none_on_pinata_http_error(self):
        """Should return None (not raise) when Pinata returns HTTP 401/500."""
        import requests as real_requests
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = real_requests.exceptions.HTTPError("401")

        with patch("web3.config.PINATA_JWT", "bad_jwt"), \
             patch("web3.config.IPFS_REQUEST_TIMEOUT", 30), \
             patch("requests.post", return_value=mock_response):
            from web3_addon.ipfs_client import upload_to_ipfs
            try:
                result = upload_to_ipfs(b"data", "file.enc")
                self.assertIsNone(result)
            except Exception as exc:
                self.fail(f"upload_to_ipfs raised an exception: {exc}")

    def test_returns_none_on_connection_error(self):
        """Should return None when the network request times out."""
        import requests as real_requests
        with patch("web3.config.PINATA_JWT", "valid_jwt"), \
             patch("web3.config.IPFS_REQUEST_TIMEOUT", 30), \
             patch("requests.post", side_effect=real_requests.exceptions.Timeout("timeout")):
            from web3_addon.ipfs_client import upload_to_ipfs
            try:
                result = upload_to_ipfs(b"data", "file.enc")
                self.assertIsNone(result)
            except Exception as exc:
                self.fail(f"upload_to_ipfs raised an exception: {exc}")

    def test_returns_none_when_response_has_no_cid(self):
        """Should return None if Pinata returns 200 but with no IpfsHash field."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}  # Missing IpfsHash
        mock_response.raise_for_status = MagicMock()

        with patch("web3.config.PINATA_JWT", "valid_jwt"), \
             patch("web3.config.IPFS_REQUEST_TIMEOUT", 30), \
             patch("requests.post", return_value=mock_response):
            from web3_addon.ipfs_client import upload_to_ipfs
            result = upload_to_ipfs(b"data", "file.enc")
            self.assertIsNone(result)


class TestDownloadFromIPFS(unittest.TestCase):
    """Tests for web3.ipfs_client.download_from_ipfs()"""

    def test_returns_none_for_empty_cid(self):
        """Should return None immediately for empty or whitespace-only CID."""
        from web3_addon.ipfs_client import download_from_ipfs
        self.assertIsNone(download_from_ipfs(""))
        self.assertIsNone(download_from_ipfs("   "))

    def test_returns_bytes_from_pinata_gateway(self):
        """Should return content from the Pinata gateway when JWT is set."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"decrypted content bytes"

        with patch("web3.config.PINATA_JWT", "valid_jwt"), \
             patch("web3.config.PINATA_GATEWAY", "https://gateway.pinata.cloud"), \
             patch("web3.config.IPFS_PUBLIC_GATEWAY", "https://ipfs.io"), \
             patch("web3.config.IPFS_REQUEST_TIMEOUT", 20), \
             patch("requests.get", return_value=mock_response):
            from web3_addon.ipfs_client import download_from_ipfs
            result = download_from_ipfs("QmSomeCID")

        self.assertEqual(result, b"decrypted content bytes")

    def test_falls_back_to_public_gateway_when_pinata_fails(self):
        """Should try the public IPFS gateway after Pinata gateway fails."""
        pinata_fail = MagicMock(status_code=503)
        public_ok   = MagicMock(status_code=200, content=b"public gateway data")

        call_count = {"n": 0}
        def mock_get(url, **kwargs):
            call_count["n"] += 1
            if "pinata" in url:
                return pinata_fail
            return public_ok

        with patch("web3.config.PINATA_JWT", "valid_jwt"), \
             patch("web3.config.PINATA_GATEWAY", "https://gateway.pinata.cloud"), \
             patch("web3.config.IPFS_PUBLIC_GATEWAY", "https://ipfs.io"), \
             patch("web3.config.IPFS_REQUEST_TIMEOUT", 20), \
             patch("requests.get", side_effect=mock_get):
            from web3_addon.ipfs_client import download_from_ipfs
            result = download_from_ipfs("QmSomeCID")

        self.assertEqual(result, b"public gateway data")
        self.assertEqual(call_count["n"], 2)  # Tried both gateways

    def test_returns_none_when_all_gateways_fail(self):
        """Should return None (not raise) when every gateway fails."""
        all_fail = MagicMock(status_code=503)

        with patch("web3.config.PINATA_JWT", "valid_jwt"), \
             patch("web3.config.PINATA_GATEWAY", "https://gateway.pinata.cloud"), \
             patch("web3.config.IPFS_PUBLIC_GATEWAY", "https://ipfs.io"), \
             patch("web3.config.IPFS_REQUEST_TIMEOUT", 20), \
             patch("requests.get", return_value=all_fail):
            from web3_addon.ipfs_client import download_from_ipfs
            try:
                result = download_from_ipfs("QmSomeCID")
                self.assertIsNone(result)
            except Exception as exc:
                self.fail(f"download_from_ipfs raised an exception: {exc}")

    def test_skips_pinata_gateway_when_no_jwt(self):
        """Should skip Pinata gateway and go directly to public gateway when no JWT."""
        public_ok = MagicMock(status_code=200, content=b"public data")
        call_urls = []

        def mock_get(url, **kwargs):
            call_urls.append(url)
            return public_ok

        with patch("web3.config.PINATA_JWT", ""), \
             patch("web3.config.PINATA_GATEWAY", "https://gateway.pinata.cloud"), \
             patch("web3.config.IPFS_PUBLIC_GATEWAY", "https://ipfs.io"), \
             patch("web3.config.IPFS_REQUEST_TIMEOUT", 20), \
             patch("requests.get", side_effect=mock_get):
            from web3_addon.ipfs_client import download_from_ipfs
            result = download_from_ipfs("QmSomeCID")

        # Should only have called the public gateway
        self.assertEqual(len(call_urls), 1)
        self.assertIn("ipfs.io", call_urls[0])
        self.assertEqual(result, b"public data")

    def test_exception_is_swallowed(self):
        """Arbitrary exception inside download_from_ipfs must NOT propagate."""
        with patch("requests.get", side_effect=RuntimeError("boom")), \
             patch("web3.config.PINATA_JWT", "jwt"), \
             patch("web3.config.PINATA_GATEWAY", "https://gateway.pinata.cloud"), \
             patch("web3.config.IPFS_PUBLIC_GATEWAY", "https://ipfs.io"), \
             patch("web3.config.IPFS_REQUEST_TIMEOUT", 20):
            from web3_addon.ipfs_client import download_from_ipfs
            try:
                result = download_from_ipfs("QmCID")
                self.assertIsNone(result)
            except Exception as exc:
                self.fail(f"download_from_ipfs raised an exception: {exc}")


if __name__ == "__main__":
    unittest.main()
