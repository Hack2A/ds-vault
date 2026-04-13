// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title VaultRegistry
 * @author ds-vault
 * @notice Minimal tamper-proof on-chain registry for ds-vault file hashes and IPFS CIDs.
 *
 * @dev  Design constraints:
 *       - No encryption logic on-chain.
 *       - No large data storage — only hashes (bytes32) and identifiers (string CID).
 *       - One record per file hash; calling storeRecord again updates the record.
 *       - The caller's address is recorded as the owner for provenance.
 *       - Compatible with Polygon, Ethereum, Arbitrum, Base, Optimism (any EVM chain).
 */
contract VaultRegistry {
    // ─── Data Structures ──────────────────────────────────────────────────────

    struct Record {
        bytes32 fileHash;   // SHA-256 of the original plaintext
        string  cid;        // IPFS Content Identifier (empty string when IPFS disabled)
        address owner;      // Wallet that submitted this record
        uint256 timestamp;  // Block timestamp at submission
    }

    // ─── State ────────────────────────────────────────────────────────────────

    /// @dev fileHash → Record. timestamp==0 means the record has never been set.
    mapping(bytes32 => Record) private _records;

    // ─── Events ───────────────────────────────────────────────────────────────

    /**
     * @notice Emitted whenever a record is stored or updated.
     * @param fileHash SHA-256 hash of the plaintext (indexed for efficient filtering).
     * @param owner    Address that submitted the record (indexed).
     * @param cid      IPFS CID (empty string when IPFS is not used).
     * @param timestamp Block timestamp at submission.
     */
    event RecordStored(
        bytes32 indexed fileHash,
        address indexed owner,
        string          cid,
        uint256         timestamp
    );

    // ─── Write Functions ──────────────────────────────────────────────────────

    /**
     * @notice Store or update a file hash and optional IPFS CID.
     *
     * @dev  fileHash must not be the zero hash. Subsequent calls with the same
     *       fileHash will overwrite the previous record — this is intentional
     *       to support re-encryption workflows.
     *
     * @param fileHash  SHA-256 hash of the original plaintext (32 bytes).
     * @param cid       IPFS Content Identifier, or empty string if IPFS is not used.
     */
    function storeRecord(bytes32 fileHash, string calldata cid) external {
        require(fileHash != bytes32(0), "VaultRegistry: zero hash rejected");

        _records[fileHash] = Record({
            fileHash:  fileHash,
            cid:       cid,
            owner:     msg.sender,
            timestamp: block.timestamp
        });

        emit RecordStored(fileHash, msg.sender, cid, block.timestamp);
    }

    // ─── Read Functions ───────────────────────────────────────────────────────

    /**
     * @notice Retrieve the full record for a file hash.
     *
     * @dev  If the record has never been stored, all fields will be zero/empty
     *       and timestamp will be 0. Use exists() to check before calling this.
     *
     * @param fileHash SHA-256 hash to look up.
     * @return record  The stored Record struct (timestamp==0 means not found).
     */
    function getRecord(bytes32 fileHash) external view returns (Record memory record) {
        return _records[fileHash];
    }

    /**
     * @notice Check whether a file hash has a record stored.
     *
     * @param fileHash SHA-256 hash to check.
     * @return bool True if a record exists (was ever stored), false otherwise.
     */
    function exists(bytes32 fileHash) external view returns (bool) {
        return _records[fileHash].timestamp != 0;
    }

    /**
     * @notice Return only the owner address for a file hash.
     *
     * @dev  Convenience view; avoids decoding the full struct when only
     *       provenance checking is needed.
     *
     * @param fileHash SHA-256 hash to look up.
     * @return owner  Address that submitted the record, or address(0) if not found.
     */
    function getOwner(bytes32 fileHash) external view returns (address owner) {
        return _records[fileHash].owner;
    }
}
