"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";

interface SessionCompleteProps {
  totalMinutes: number;
  segmentCount: number;
  /**
   * Readiness percentage after the session (0–100).
   * Rendered as a plain number — no delta animation, no celebratory framing.
   * Design principle: calm summary only. See Stride product principles (2026-07-04).
   */
  readinessAfter: number;
}

/**
 * SessionComplete — calm session summary screen.
 *
 * Design principles applied:
 * - NO praise phrases ("great job", "well done", "amazing", "congrats")
 * - NO exclamation marks
 * - NO emoji
 * - NO animation on the readiness number
 * - Numbers rendered in font-mono for readability
 *
 * Copy tone: factual, informative, respectful of the student's time.
 */
export function SessionComplete({
  totalMinutes,
  segmentCount,
  readinessAfter,
}: SessionCompleteProps) {
  return (
    <section
      role="region"
      aria-label="Session complete"
      className="max-w-[560px] mx-auto pt-24 text-center space-y-8"
    >
      <h1 className="text-[32px] font-sans text-white">
        Today's Session Complete
      </h1>

      <ul className="text-[16px] text-white/80 space-y-1 list-none">
        <li>
          <span className="font-mono">{totalMinutes}</span> minutes
        </li>
        <li>
          <span className="font-mono">{segmentCount}</span> segments completed
        </li>
        <li>
          Readiness updated to{" "}
          <span className="font-mono">{Math.round(readinessAfter)}%</span>
        </li>
      </ul>

      <div className="flex flex-col items-center gap-3">
        <Link href="/progress">
          <Button variant="primary">Review your progress →</Button>
        </Link>
        <Link
          href="/"
          className="text-[12px] text-white/60 hover:text-white/80 transition-colors"
        >
          Back to home
        </Link>
      </div>
    </section>
  );
}
