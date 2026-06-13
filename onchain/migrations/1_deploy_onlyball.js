const OnlyBall = artifacts.require("OnlyBall");

// Deployment parameters (override via env).
//   FUDSX_ADDRESS    deployed FUDSX TRC20 (base58)
//   TICKET_PRICE     FUDSX per ticket, whole tokens (default 200)
//   DRAW_INTERVAL    seconds between draws (default 86400 = 1 day)
const FUDSX = process.env.FUDSX_ADDRESS || "TPF44Br5XkJw6snvo3URN4CT7UALJZggtG";
const TICKET_PRICE = process.env.TICKET_PRICE || "200";
const DRAW_INTERVAL = process.env.DRAW_INTERVAL || "86400";

module.exports = function (deployer) {
  // FUDSX has 18 decimals.
  const priceWei = BigInt(TICKET_PRICE) * 10n ** 18n;
  deployer.deploy(OnlyBall, FUDSX, priceWei.toString(), DRAW_INTERVAL);
};
