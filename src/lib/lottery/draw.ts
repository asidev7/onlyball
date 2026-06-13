// Lottery helpers: number validation, quick-pick, match checking, mock data.

import { NUMBERS_TO_PICK, MAX_NUMBER } from "@/lib/constants/config";

export function validateNumbers(nums: number[]): boolean {
  if (nums.length !== NUMBERS_TO_PICK) return false;
  if (new Set(nums).size !== NUMBERS_TO_PICK) return false;
  return nums.every((n) => n >= 1 && n <= MAX_NUMBER);
}

/** Random 6 unique numbers in [1, 49], sorted ascending. */
export function quickPick(): number[] {
  const pool = new Set<number>();
  while (pool.size < NUMBERS_TO_PICK) {
    pool.add(Math.floor(Math.random() * MAX_NUMBER) + 1);
  }
  return Array.from(pool).sort((a, b) => a - b);
}

export function countMatches(picked: number[], winning: number[]): number {
  const w = new Set(winning);
  return picked.filter((n) => w.has(n)).length;
}

export function isJackpotWin(picked: number[], winning: number[]): boolean {
  return countMatches(picked, winning) === NUMBERS_TO_PICK;
}

// Draw result shape shared by the results pages (data comes from the API).
export interface DrawResult {
  round: number;
  date: string; // ISO
  numbers: number[];
  jackpot: number; // FUDSX
  winner: string | null; // base58 or null (rollover)
  txHash: string | null;
  totalTickets: number;
}
