"use client";

import { motion } from "framer-motion";
import NumberBall from "@/components/ui/NumberBall";

type Size = "sm" | "md" | "lg";

// Animated row of result balls (they drop in one by one).
export default function BallDisplay({
  numbers,
  size = "md",
  animate = true,
  variant = "winning",
}: {
  numbers: number[];
  size?: Size;
  animate?: boolean;
  variant?: "winning" | "default" | "gold";
}) {
  return (
    <div className="flex flex-wrap items-center gap-2 sm:gap-3">
      {numbers.map((n, i) => (
        <motion.div
          key={`${n}-${i}`}
          initial={animate ? { y: -24, opacity: 0 } : false}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: animate ? i * 0.12 : 0, type: "spring", stiffness: 300, damping: 16 }}
        >
          <NumberBall n={n} size={size} variant={variant} />
        </motion.div>
      ))}
    </div>
  );
}
