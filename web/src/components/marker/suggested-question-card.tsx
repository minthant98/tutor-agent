"use client";
import { useRouter } from "next/navigation";
import type { MarkerV3LandingData } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface SuggestedQuestionCardProps {
  question: MarkerV3LandingData["question"];
  refreshCountUsed: number;
  refreshLimit: number | null;
  tier: "free" | "pro";
  onRefresh: () => void;
}

export function SuggestedQuestionCard({
  question,
  refreshCountUsed,
  refreshLimit,
  tier,
  onRefresh,
}: SuggestedQuestionCardProps) {
  const router = useRouter();
  const refreshesRemaining =
    refreshLimit !== null ? Math.max(0, refreshLimit - refreshCountUsed) : null;

  return (
    <Card data-surface="2" className="space-y-4">
      {/* Header row: marks chip + paper ref */}
      <div className="flex items-start gap-3">
        <Badge variant="secondary" className="shrink-0 font-mono">
          {question.max_marks} marks
        </Badge>
        <span className="text-[12px] text-[var(--text-secondary)] leading-tight mt-0.5">
          {question.paper_ref}
        </span>
      </div>

      {/* Question text */}
      <p className="text-[14px] leading-relaxed whitespace-pre-wrap text-[var(--text-primary)]">
        {question.text}
      </p>

      {/* CTAs */}
      <div className="flex flex-col gap-2 pt-1">
        <Button
          variant="primary"
          size="md"
          onClick={() => router.push(`/mark/new?question_id=${question.id}`)}
        >
          Submit an answer to this question
        </Button>

        {/* Ghost refresh button — hidden for pro */}
        {tier === "free" && refreshesRemaining !== null && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onRefresh}
            disabled={refreshesRemaining <= 0}
          >
            Different Question · {refreshesRemaining} free refresh
            {refreshesRemaining !== 1 ? "es" : ""} remaining
          </Button>
        )}
      </div>
    </Card>
  );
}
