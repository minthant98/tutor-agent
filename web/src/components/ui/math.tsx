"use client";

import "katex/dist/katex.min.css";
import { InlineMath, BlockMath } from "react-katex";

interface MathProps {
  tex: string;
  inline?: boolean;
}

/**
 * Math — KaTeX renderer for LaTeX expressions.
 *
 * Uses InlineMath for inline expressions and BlockMath for display-mode.
 * Importing katex.min.css here ensures styles load alongside the component.
 */
export function Math({ tex, inline = false }: MathProps) {
  return (
    <span data-testid="math">
      {inline ? <InlineMath math={tex} /> : <BlockMath math={tex} />}
    </span>
  );
}
