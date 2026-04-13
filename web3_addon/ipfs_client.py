"""
web3/ipfs_client.py — IPFS integration for ds-vault via Pinata.

Upload strategy (waterfall):
    1. Pinata API (authenticated, pinned) — requires PINATA_JWT
    2. Failure → returns None (CID stored as "" in metadata)

Download strategy (waterfall):
    1. Pinata dedicated gateway (fastest, if PINATA_JWT is set)
    2. Public IPFS gateway (ipfs.io) — fallback
    3. Failure → returns None

All failures are non-blocking. IPFS errors NEVER prevent vault operations.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def upload_to_ipfs(data: bytes, filename: str = "vault_encrypted_file") -> Optional[str]:
    """Upload encrypted bytes to IPFS via Pinata and return the CID.

    Parameters
    ----------
    data : bytes
        Raw bytes to pin (typically the encrypted vault data).
    filename : str, optional
        Logical filename shown in the Pinata dashboard (no security impact).

    Returns
    -------
    str | None
        IPFS Content Identifier (CIDv0 or CIDv1) on success, None on failure.
    """
    try:
        import requests
        from web3_addon.config import PINATA_JWT, IPFS_REQUEST_TIMEOUT

        if not PINATA_JWT:
            logger.info("PINATA_JWT not configured — IPFS upload skipped.")
            return None

        url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
        headers = {"Authorization": f"Bearer {PINATA_JWT}"}

        # Pinata expects multipart/form-data with optional metadata JSON
        files = {"file": (filename, data, "application/octet-stream")}
        payload = {
            "pinataMetadata": f'{{"name": "{filename}"}}',
            "pinataOptions": '{"cidVersion": 1}',
        }

        resp = requests.post(
            url,
            headers=headers,
            files=files,
            data=payload,
            timeout=IPFS_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()

        cid = resp.json().get("IpfsHash", "").strip()
        if cid:
            logger.info("Pinned to IPFS: %s", cid)
            return cid

        logger.warning("Pinata returned no IpfsHash in response.")
        return None

    except Exception as exc:
        logger.warning("IPFS upload failed (non-blocking, vault continues): %s", exc)
        return None


def download_from_ipfs(cid: str) -> Optional[bytes]:
    """Download content from IPFS by CID using a gateway waterfall.

    Gateway order:
        1. Pinata dedicated gateway (if PINATA_JWT is set)
        2. Public IPFS gateway (ipfs.io)

    Parameters
    ----------
    cid : str
        IPFS Content Identifier.

    Returns
    -------
    bytes | None
        File bytes on success, None if all gateways fail.
    """
    if not cid or not cid.strip():
        return None

    try:
        import requests
        from web3_addon.config import PINATA_GATEWAY, IPFS_PUBLIC_GATEWAY, PINATA_JWT, IPFS_REQUEST_TIMEOUT

        # Build ordered gateway list
        gateways: list[str] = []
        if PINATA_JWT:
            # Pinata dedicated gateway — fastest and most reliable
            gateways.append(f"{PINATA_GATEWAY.rstrip('/')}/ipfs/{cid}")
        # Public IPFS gateway — always available as final fallback
        gateways.append(f"{IPFS_PUBLIC_GATEWAY.rstrip('/')}/ipfs/{cid}")

        for gateway_url in gateways:
            try:
                resp = requests.get(gateway_url, timeout=IPFS_REQUEST_TIMEOUT)
                if resp.status_code == 200:
                    logger.info(
                        "Downloaded from IPFS via %s (CID: %s)",
                        gateway_url.split("/ipfs/")[0],
                        cid[:20],
                    )
                    return resp.content
                logger.warning(
                    "Gateway returned HTTP %s: %s", resp.status_code, gateway_url
                )
            except Exception as gateway_exc:
                logger.warning("Gateway failed (%s): %s", gateway_url, gateway_exc)

        logger.error("All IPFS gateways failed for CID: %s", cid[:20])
        return None

    except Exception as exc:
        logger.error("download_from_ipfs failed: %s", exc)
        return None


def pin_status(cid: str) -> Optional[dict]:
    """Check the pin status of a CID on Pinata.

    Parameters
    ----------
    cid : str
        IPFS Content Identifier.

    Returns
    -------
    dict | None
        Pinata pin status dict or None if not found / error.
    """
    try:
        import requests
        from web3_addon.config import PINATA_JWT

        if not PINATA_JWT:
            return None

        url = f"https://api.pinata.cloud/pinning/pinJobs?ipfs_pin_hash={cid}"
        headers = {"Authorization": f"Bearer {PINATA_JWT}"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        rows = resp.json().get("rows", [])
        return rows[0] if rows else None

    except Exception as exc:
        logger.warning("pin_status check failed: %s", exc)
        return None
