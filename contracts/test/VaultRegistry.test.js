const { expect } = require("chai");
const { ethers } = require("hardhat");
const { loadFixture } = require("@nomicfoundation/hardhat-network-helpers");

describe("VaultRegistry", function () {
  // ─── Fixture ──────────────────────────────────────────────────────────────

  async function deployFixture() {
    const [owner, alice, bob] = await ethers.getSigners();
    const VaultRegistry = await ethers.getContractFactory("VaultRegistry");
    const registry = await VaultRegistry.deploy();
    await registry.waitForDeployment();

    // A realistic SHA-256 hex hash (32 bytes)
    const fileHash = ethers.encodeBytes32String(""); // zero — but we'll use real hashes below
    const realHash = "0x" + "ab".repeat(32); // 32-byte hex for testing

    return { registry, owner, alice, bob, realHash };
  }

  // ─── Deployment ───────────────────────────────────────────────────────────

  describe("Deployment", function () {
    it("Should deploy without errors", async function () {
      const { registry } = await loadFixture(deployFixture);
      expect(await registry.getAddress()).to.be.a("string").and.match(/^0x/);
    });
  });

  // ─── storeRecord ──────────────────────────────────────────────────────────

  describe("storeRecord()", function () {
    it("Should store a record and emit RecordStored event", async function () {
      const { registry, owner, realHash } = await loadFixture(deployFixture);
      const cid = "QmTestCID123";

      await expect(registry.storeRecord(realHash, cid))
        .to.emit(registry, "RecordStored")
        .withArgs(realHash, owner.address, cid, await getBlockTimestamp());
    });

    it("Should store a record with empty CID (IPFS disabled)", async function () {
      const { registry, realHash } = await loadFixture(deployFixture);
      await expect(registry.storeRecord(realHash, "")).to.not.be.reverted;
    });

    it("Should allow updating an existing record", async function () {
      const { registry, realHash } = await loadFixture(deployFixture);
      await registry.storeRecord(realHash, "CID_v1");
      await registry.storeRecord(realHash, "CID_v2");
      const record = await registry.getRecord(realHash);
      expect(record.cid).to.equal("CID_v2");
    });

    it("Should reject the zero hash", async function () {
      const { registry } = await loadFixture(deployFixture);
      const zeroHash = "0x" + "00".repeat(32);
      await expect(registry.storeRecord(zeroHash, "")).to.be.revertedWith(
        "VaultRegistry: zero hash rejected"
      );
    });

    it("Should record the correct owner address", async function () {
      const { registry, realHash, alice } = await loadFixture(deployFixture);
      await registry.connect(alice).storeRecord(realHash, "CID_alice");
      expect(await registry.getOwner(realHash)).to.equal(alice.address);
    });

    it("Should allow different users to store different hashes", async function () {
      const { registry, alice, bob } = await loadFixture(deployFixture);
      const hashAlice = "0x" + "aa".repeat(32);
      const hashBob   = "0x" + "bb".repeat(32);
      await registry.connect(alice).storeRecord(hashAlice, "CID_A");
      await registry.connect(bob).storeRecord(hashBob, "CID_B");
      expect((await registry.getRecord(hashAlice)).cid).to.equal("CID_A");
      expect((await registry.getRecord(hashBob)).cid).to.equal("CID_B");
    });
  });

  // ─── getRecord ────────────────────────────────────────────────────────────

  describe("getRecord()", function () {
    it("Should return the stored CID and owner", async function () {
      const { registry, owner, realHash } = await loadFixture(deployFixture);
      await registry.storeRecord(realHash, "QmExampleCID");
      const record = await registry.getRecord(realHash);
      expect(record.cid).to.equal("QmExampleCID");
      expect(record.owner).to.equal(owner.address);
      expect(record.fileHash).to.equal(realHash);
    });

    it("Should return timestamp > 0 after storing", async function () {
      const { registry, realHash } = await loadFixture(deployFixture);
      await registry.storeRecord(realHash, "");
      const record = await registry.getRecord(realHash);
      expect(record.timestamp).to.be.greaterThan(0n);
    });

    it("Should return zero timestamp for unknown hash", async function () {
      const { registry } = await loadFixture(deployFixture);
      const unknownHash = "0x" + "cc".repeat(32);
      const record = await registry.getRecord(unknownHash);
      expect(record.timestamp).to.equal(0n);
    });
  });

  // ─── exists ───────────────────────────────────────────────────────────────

  describe("exists()", function () {
    it("Should return false for an unstored hash", async function () {
      const { registry } = await loadFixture(deployFixture);
      const unknownHash = "0x" + "dd".repeat(32);
      expect(await registry.exists(unknownHash)).to.be.false;
    });

    it("Should return true after storeRecord", async function () {
      const { registry, realHash } = await loadFixture(deployFixture);
      await registry.storeRecord(realHash, "");
      expect(await registry.exists(realHash)).to.be.true;
    });
  });

  // ─── getOwner ─────────────────────────────────────────────────────────────

  describe("getOwner()", function () {
    it("Should return address(0) for unknown hash", async function () {
      const { registry } = await loadFixture(deployFixture);
      const unknownHash = "0x" + "ee".repeat(32);
      expect(await registry.getOwner(unknownHash)).to.equal(ethers.ZeroAddress);
    });

    it("Should return the correct owner after storing", async function () {
      const { registry, alice, realHash } = await loadFixture(deployFixture);
      await registry.connect(alice).storeRecord(realHash, "");
      expect(await registry.getOwner(realHash)).to.equal(alice.address);
    });
  });

  // ─── Gas Usage ────────────────────────────────────────────────────────────

  describe("Gas usage", function () {
    it("storeRecord should use less than 150000 gas", async function () {
      const { registry, realHash } = await loadFixture(deployFixture);
      const tx = await registry.storeRecord(realHash, "QmGasTestCID");
      const receipt = await tx.wait();
      expect(receipt.gasUsed).to.be.lessThan(150000n);
    });
  });
});

// ─── Helper ───────────────────────────────────────────────────────────────────

async function getBlockTimestamp() {
  // Returns approximate next block timestamp — good enough for event matching
  const block = await ethers.provider.getBlock("latest");
  return block.timestamp + 1;
}
