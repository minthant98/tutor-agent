"use client";

import { TeachBlock, type TeachBlockData } from "./teach-block";
import { ReinforceBlock, type ReinforceStep } from "./reinforce-block";
import { AssessBlock, type AssessQuestion } from "./assess-block";

// Re-export types so consumers import from one place
export type { TeachBlockData, ReinforceStep, AssessQuestion };

export type Segment =
  | { intent: "teach"; blocks: TeachBlockData[] }
  | { intent: "reinforce"; steps: ReinforceStep[]; followUp?: AssessQuestion }
  | { intent: "assess"; question: AssessQuestion };

interface SessionContentProps {
  segment: Segment;
}

/**
 * SessionContent — switches on segment.intent to render the appropriate block.
 *
 * teach    → TeachBlock    (prose + math + callouts, 800px max-width)
 * reinforce → ReinforceBlock (keyboard-driven step reveal, 800px max-width)
 * assess   → AssessBlock   (question + marks chip, 880px max-width)
 *
 * NOTE (Task 10): Content is consumed via prop. Backend plumbing that provides
 * real segment data is a future concern — the session page passes mock segments
 * until the API contract is established.
 */
export function SessionContent({ segment }: SessionContentProps) {
  switch (segment.intent) {
    case "teach":
      return <TeachBlock blocks={segment.blocks} />;

    case "reinforce":
      return (
        <ReinforceBlock steps={segment.steps} followUp={segment.followUp} />
      );

    case "assess":
      return <AssessBlock question={segment.question} />;

    default:
      return null;
  }
}
