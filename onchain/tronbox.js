// TronBox configuration for the OnlyBall lottery contract.
//
// Secrets are read from the environment — never commit your private key.
//   PRIVATE_KEY_MAINNET   deployer key (TRX for energy/bandwidth)
//   PRIVATE_KEY_SHASTA    deployer key for the Shasta testnet
//
// Deploy:  npm run deploy:shasta   (test first!)   then   npm run deploy:mainnet

// Load onchain/.env (KEY=VALUE) without a dependency.
const fs = require("fs");
const path = require("path");
const envPath = path.join(__dirname, ".env");
if (fs.existsSync(envPath)) {
  for (const line of fs.readFileSync(envPath, "utf8").split("\n")) {
    const s = line.trim();
    if (!s || s.startsWith("#") || !s.includes("=")) continue;
    const idx = s.indexOf("=");
    const k = s.slice(0, idx).trim();
    const v = s.slice(idx + 1).trim();
    if (!(k in process.env)) process.env[k] = v;
  }
}

const port = process.env.HOST_PORT || 9090;

module.exports = {
  networks: {
    mainnet: {
      privateKey: process.env.PRIVATE_KEY_MAINNET,
      userFeePercentage: 100,
      feeLimit: 1500 * 1e6,
      fullHost: "https://api.trongrid.io",
      network_id: "1",
    },
    shasta: {
      privateKey: process.env.PRIVATE_KEY_SHASTA,
      userFeePercentage: 50,
      feeLimit: 1500 * 1e6,
      fullHost: "https://api.shasta.trongrid.io",
      network_id: "2",
    },
    development: {
      privateKey:
        process.env.PRIVATE_KEY_DEV ||
        "0000000000000000000000000000000000000000000000000000000000000001",
      userFeePercentage: 0,
      feeLimit: 1000 * 1e6,
      fullHost: "http://127.0.0.1:" + port,
      network_id: "9",
    },
  },
  compilers: {
    solc: {
      version: "0.8.25",
      settings: {
        optimizer: { enabled: true, runs: 200 },
      },
    },
  },
};
