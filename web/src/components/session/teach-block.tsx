"use client";

import { Math } from "@/components/ui/math";

export type TeachBlockData =
  | { type: "prose"; text: string }
  | { type: "math"; tex: string }
  | { type: "callout"; text: string };

interface TeachBlockProps {
  blocks: TeachBlockData[];
}

/**
 * TeachBlock — renders a teach-intent segment as rich prose.
 *
 * Layout: 800px max-width centered, 128px vertical padding, 16px body text
 * with 1.6 line-height. Targets 65–75 chars per line.
 *
 * Block types:
 *   prose   → <p> with default body styling
 *   math    → KaTeX display math via <Math>
 *   callout → bordered aside with surface-1 background and mark-scheme tint
 */
export function TeachBlock({ blocks }: TeachBlockProps) {
  return (
    <article className="max-w-[800px] mx-auto py-16 space-y-6 text-[16px] font-sans leading-[1.6]">
      {blocks.map((block, i) => {
        if (block.type === "prose") {
          return (
            <p key={i} className="text-[var(--text-primary)]">
              {block.text}
            </p>
          );
        }

        if (block.type === "math") {
          return <Math key={i} tex={block.tex} />;
        }

        if (block.type === "callout") {
          return (
            <div
              key={i}
              className="border border-[var(--border-subtle)] rounded-lg p-4 bg-[var(--surface-1)] text-[var(--color-markScheme)]"
            >
              {block.text}
            </div>
          );
        }

        return null;
      })}
    </article>
  );
}
