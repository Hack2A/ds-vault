/**
 * deploy.js — VaultRegistry deployment script.
 *
 * Usage:
 *   npm run deploy:amoy        Deploy to Polygon Amoy testnet
 *   npm run deploy:sepolia     Deploy to Ethereum Sepolia
 *   npm run deploy:arbitrum    Deploy to Arbitrum Sepolia
 *   npm run deploy:base        Deploy to Base Sepolia
 *   npm run deploy:optimism    Deploy to Optimism Sepolia
 *   npm run deploy:polygon     Deploy to Polygon Mainnet (PRODUCTION)
 *   npm run deploy:local       Deploy to local Hardhat node
 *
 * After deploying, copy the printed contract address into your .env.web3 file
 * using the appropriate variable (e.g., POLYGON_AMOY_CONTRACT_ADDRESS).
 */

const { ethers, network } = require("hardhat");

// Map Hardhat network name → .env.web3 variable name to set
const ENV_VAR_MAP = {
  polygon_amoy:      "POLYGON_AMOY_CONTRACT_ADDRESS",
  polygon_mainnet:   "POLYGON_CONTRACT_ADDRESS",
  ethereum_sepolia:  "SEPOLIA_CONTRACT_ADDRESS",
  arbitrum_sepolia:  "ARBITRUM_SEPOLIA_CONTRACT_ADDRESS",
  base_sepolia:      "BASE_SEPOLIA_CONTRACT_ADDRESS",
  optimism_sepolia:  "OPTIMISM_SEPOLIA_CONTRACT_ADDRESS",
  hardhat:           "(local — not needed in .env.web3)",
  localhost:         "(local — not needed in .env.web3)",
};

async function main() {
  const [deployer] = await ethers.getSigners();
  const networkName = network.name;

  console.log("\n╔══════════════════════════════════════════════════╗");
  console.log("║          ds-vault — VaultRegistry Deploy         ║");
  console.log("╚══════════════════════════════════════════════════╝\n");
  console.log(`  Network  : ${networkName}`);
  console.log(`  Deployer : ${deployer.address}`);

  // Check deployer balance (warn if low on testnets)
  const balance = await ethers.provider.getBalance(deployer.address);
  const balanceEth = ethers.formatEther(balance);
  console.log(`  Balance  : ${balanceEth} ETH/MATIC`);

  if (parseFloat(balanceEth) < 0.01 && networkName !== "hardhat" && networkName !== "localhost") {
    console.warn("\n⚠  WARNING: Deployer balance is very low. The transaction may fail.");
    console.warn("   Get testnet tokens from the network faucet before deploying.\n");
  }

  console.log("\n  Deploying VaultRegistry...");

  const VaultRegistry = await ethers.getContractFactory("VaultRegistry");
  const contract = await VaultRegistry.deploy();
  await contract.waitForDeployment();

  const contractAddress = await contract.getAddress();

  console.log("\n  ✅ VaultRegistry deployed successfully!\n");
  console.log("  ┌─────────────────────────────────────────────────┐");
  console.log(`  │  Contract Address : ${contractAddress}`);
  console.log("  └─────────────────────────────────────────────────┘");

  const envVar = ENV_VAR_MAP[networkName] || `${networkName.toUpperCase()}_CONTRACT_ADDRESS`;
  console.log(`\n  Add this to your .env.web3 file:`);
  console.log(`  ${envVar}=${contractAddress}`);
  console.log(`  ACTIVE_CHAIN=${networkName}`);
  console.log(`  USE_BLOCKCHAIN=true\n`);

  // Print block explorer link if available
  const explorers = {
    polygon_amoy:      `https://amoy.polygonscan.com/address/${contractAddress}`,
    polygon_mainnet:   `https://polygonscan.com/address/${contractAddress}`,
    ethereum_sepolia:  `https://sepolia.etherscan.io/address/${contractAddress}`,
    arbitrum_sepolia:  `https://sepolia.arbiscan.io/address/${contractAddress}`,
    base_sepolia:      `https://sepolia.basescan.org/address/${contractAddress}`,
    optimism_sepolia:  `https://sepolia-optimism.etherscan.io/address/${contractAddress}`,
  };

  if (explorers[networkName]) {
    console.log(`  Explorer: ${explorers[networkName]}\n`);
  }

  // Verify instructions
  if (networkName !== "hardhat" && networkName !== "localhost") {
    console.log("  To verify on block explorer (optional):");
    console.log(`  npx hardhat verify --network ${networkName} ${contractAddress}\n`);
  }

  return contractAddress;
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("\n  ❌ Deployment failed:", error.message);
    process.exit(1);
  });
