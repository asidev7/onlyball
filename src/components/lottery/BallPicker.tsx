"use client";

import { Shuffle, Eraser } from "lucide-react";
import { motion } from "framer-motion";
import { useLotteryStore } from "@/store/lotteryStore";
import { MAX_NUMBER, NUMBERS_TO_PICK } from "@/lib/constants/config";
import Button from "@/components/ui/Button";

export default function BallPicker() {
  const { selected, toggle, quickPick, clear } = useLotteryStore();
  const numbers = Array.from({ length: MAX_NUMBER }, (_, i) => i + 1);
  const full = selected.length >= NUMBERS_TO_PICK;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <p className="font-head text-sm text-white">
          Pick your 6 numbers{" "}
          <span className="text-[#6B7280]">
            ({selected.length}/{NUMBERS_TO_PICK})
          </span>
        </p>
        <div className="flex gap-2">
          <Button variant="dark" size="sm" onClick={quickPick} icon={<Shuffle className="h-3.5 w-3.5" />}>
            Quick pick
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={clear}
            disabled={selected.length === 0}
            icon={<Eraser className="h-3.5 w-3.5" />}
          >
            Clear
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-7 gap-2 sm:grid-cols-10">
        {numbers.map((n) => {
          const isSel = selected.includes(n);
          const disabled = !isSel && full;
          return (
            <motion.button
              key={n}
              whileTap={{ scale: 0.9 }}
              animate={isSel ? { scale: 1.08 } : { scale: 1 }}
              transition={{ type: "spring", stiffness: 500, damping: 18 }}
              onClick={() => toggle(n)}
              disabled={disabled}
              className={[
                "ob-ball aspect-square w-full text-lg leading-none transition-colors",
                isSel
                  ? "bg-[#E31C25] text-white"
                  : "bg-[#1A1A1A] text-white/80 border border-white/10",
                disabled ? "cursor-not-allowed opacity-30" : "cursor-pointer hover:border-[#E31C25]",
              ].join(" ")}
            >
              {n}
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}
