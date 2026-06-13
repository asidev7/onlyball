"use client";

// Countdown to the next draw. Uses the on-chain nextDrawTime when available,
// otherwise falls back to the next midnight UTC.
import { useEffect, useState } from "react";

export interface TimeLeft {
  h: number;
  m: number;
  s: number;
  total: number; // ms
}

function nextMidnightUTC(): number {
  const now = new Date();
  const midnight = new Date(now);
  midnight.setUTCHours(24, 0, 0, 0);
  return midnight.getTime();
}

export function useCountdown(targetMs?: number): TimeLeft {
  const compute = (): TimeLeft => {
    const target = targetMs && targetMs > Date.now() ? targetMs : nextMidnightUTC();
    const diff = Math.max(0, target - Date.now());
    return {
      h: Math.floor(diff / 3_600_000),
      m: Math.floor((diff % 3_600_000) / 60_000),
      s: Math.floor((diff % 60_000) / 1000),
      total: diff,
    };
  };

  // Start from a deterministic value so the server-rendered HTML and the
  // client's first render match (avoids a hydration mismatch on the ticking
  // seconds). The real remaining time is filled in right after mount.
  const [timeLeft, setTimeLeft] = useState<TimeLeft>({ h: 0, m: 0, s: 0, total: 0 });

  useEffect(() => {
    setTimeLeft(compute());
    const id = setInterval(() => setTimeLeft(compute()), 1000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [targetMs]);

  return timeLeft;
}
