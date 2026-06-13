"use client";

// Zustand store for the play screen: the player's number selection + referral.
import { create } from "zustand";
import { NUMBERS_TO_PICK } from "@/lib/constants/config";
import { quickPick as randomPick } from "@/lib/lottery/draw";

interface LotteryState {
  selected: number[];
  referralCode: string;
  toggle: (n: number) => void;
  quickPick: () => void;
  clear: () => void;
  setReferral: (code: string) => void;
  isComplete: () => boolean;
}

export const useLotteryStore = create<LotteryState>((set, get) => ({
  selected: [],
  referralCode: "",
  toggle: (n) =>
    set((s) => {
      if (s.selected.includes(n)) {
        return { selected: s.selected.filter((x) => x !== n) };
      }
      if (s.selected.length >= NUMBERS_TO_PICK) return s;
      return { selected: [...s.selected, n].sort((a, b) => a - b) };
    }),
  quickPick: () => set({ selected: randomPick() }),
  clear: () => set({ selected: [] }),
  setReferral: (code) => set({ referralCode: code }),
  isComplete: () => get().selected.length === NUMBERS_TO_PICK,
}));
