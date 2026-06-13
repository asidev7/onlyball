// Contract instance loaders for FUDSX, USDT and OnlyBall.

import {
  TRC20_ABI,
  ONLYBALL_ABI,
  FUDSX_ADDRESS,
  USDT_TRC20,
  ONLYBALL_ADDRESS,
} from "@/lib/constants/contract";

export async function loadFUDSX(tronWeb: TronWebInstance): Promise<TronContractInstance> {
  return tronWeb.contract(TRC20_ABI as unknown as unknown[]).at(FUDSX_ADDRESS);
}

export async function loadUSDT(tronWeb: TronWebInstance): Promise<TronContractInstance> {
  return tronWeb.contract(TRC20_ABI as unknown as unknown[]).at(USDT_TRC20);
}

export async function loadOnlyBall(
  tronWeb: TronWebInstance
): Promise<TronContractInstance | null> {
  if (!ONLYBALL_ADDRESS) return null;
  return tronWeb.contract(ONLYBALL_ABI as unknown as unknown[]).at(ONLYBALL_ADDRESS);
}
