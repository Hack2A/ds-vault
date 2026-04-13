require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config({ path: "../.env.web3" });

// ─── Load secrets from .env.web3 (project root) ───────────────────────────────
// NEVER commit real private keys. Use .env.web3 which is git-ignored.
const PRIVATE_KEY = process.env.VAULT_PRIVATE_KEY || "0x" + "0".repeat(64);

// ─── Optional Etherscan / block explorer API keys (for contract verification) ─
const POLYGONSCAN_KEY  = process.env.POLYGONSCAN_API_KEY  || "";
const ETHERSCAN_KEY    = process.env.ETHERSCAN_API_KEY    || "";
const ARBISCAN_KEY     = process.env.ARBISCAN_API_KEY     || "";
const BASESCAN_KEY     = process.env.BASESCAN_API_KEY     || "";
const OPTIMISMSCAN_KEY = process.env.OPTIMISM_API_KEY     || "";

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.19",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
      viaIR: false,
    },
  },

  // ─── Networks ───────────────────────────────────────────────────────────────
  networks: {
    // Local Hardhat node (default for tests + local deploy)
    hardhat: {
      chainId: 31337,
    },

    // ── Polygon ────────────────────────────────────────────────────────────
    polygon_amoy: {
      url: process.env.POLYGON_AMOY_RPC || "https://rpc-amoy.polygon.technology",
      chainId: 80002,
      accounts: [PRIVATE_KEY],
    },
    polygon_mainnet: {
      url: process.env.POLYGON_RPC || "https://polygon-rpc.com",
      chainId: 137,
      accounts: [PRIVATE_KEY],
    },

    // ── Ethereum ───────────────────────────────────────────────────────────
    ethereum_sepolia: {
      url: process.env.SEPOLIA_RPC || "https://rpc.sepolia.org",
      chainId: 11155111,
      accounts: [PRIVATE_KEY],
    },

    // ── Arbitrum ───────────────────────────────────────────────────────────
    arbitrum_sepolia: {
      url: process.env.ARBITRUM_SEPOLIA_RPC || "https://sepolia-rollup.arbitrum.io/rpc",
      chainId: 421614,
      accounts: [PRIVATE_KEY],
    },

    // ── Base ───────────────────────────────────────────────────────────────
    base_sepolia: {
      url: process.env.BASE_SEPOLIA_RPC || "https://sepolia.base.org",
      chainId: 84532,
      accounts: [PRIVATE_KEY],
    },

    // ── Optimism ───────────────────────────────────────────────────────────
    optimism_sepolia: {
      url: process.env.OPTIMISM_SEPOLIA_RPC || "https://sepolia.optimism.io",
      chainId: 11155420,
      accounts: [PRIVATE_KEY],
    },
  },

  // ─── Block Explorer Verification ────────────────────────────────────────────
  etherscan: {
    apiKey: {
      polygon:           POLYGONSCAN_KEY,
      polygonAmoy:       POLYGONSCAN_KEY,
      mainnet:           ETHERSCAN_KEY,
      sepolia:           ETHERSCAN_KEY,
      arbitrumSepolia:   ARBISCAN_KEY,
      baseSepolia:       BASESCAN_KEY,
      optimismSepolia:   OPTIMISMSCAN_KEY,
    },
    customChains: [
      {
        network: "polygonAmoy",
        chainId: 80002,
        urls: {
          apiURL: "https://api-amoy.polygonscan.com/api",
          browserURL: "https://amoy.polygonscan.com",
        },
      },
      {
        network: "arbitrumSepolia",
        chainId: 421614,
        urls: {
          apiURL: "https://api-sepolia.arbiscan.io/api",
          browserURL: "https://sepolia.arbiscan.io",
        },
      },
      {
        network: "baseSepolia",
        chainId: 84532,
        urls: {
          apiURL: "https://api-sepolia.basescan.org/api",
          browserURL: "https://sepolia.basescan.org",
        },
      },
      {
        network: "optimismSepolia",
        chainId: 11155420,
        urls: {
          apiURL: "https://api-sepolia-optimistic.etherscan.io/api",
          browserURL: "https://sepolia-optimism.etherscan.io",
        },
      },
    ],
  },

  // ─── Gas Reporter ───────────────────────────────────────────────────────────
  gasReporter: {
    enabled: process.env.REPORT_GAS === "true",
    currency: "USD",
    coinmarketcap: process.env.COINMARKETCAP_API_KEY || "",
  },

  // ─── Coverage ───────────────────────────────────────────────────────────────
  // Run: npm run test:coverage
  mocha: {
    timeout: 60000,
  },
};
