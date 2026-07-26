"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

export type DifficultyBucket = "any" | "easy" | "medium" | "hard";
export type StatusFilter = "all" | "graded" | "error" | "pending";

function difficultyToLabel(d: DifficultyBucket): string {
  switch (d) {
    case "any":
      return "Any";
    case "easy":
      return "≤3 marks";
    case "medium":
      return "4–6";
    case "hard":
      return "7+";
  }
}

function statusToLabel(s: StatusFilter): string {
  switch (s) {
    case "all":
      return "All";
    case "graded":
      return "Graded";
    case "error":
      return "Error";
    case "pending":
      return "Pending";
  }
}

const DIFFICULTY_OPTIONS: DifficultyBucket[] = ["any", "easy", "medium", "hard"];
const STATUS_OPTIONS: StatusFilter[] = ["all", "graded", "error", "pending"];

export function HistoryFilters() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const currentDifficulty = (searchParams.get("difficulty") as DifficultyBucket) ?? "any";
  const currentStatus = (searchParams.get("status") as StatusFilter) ?? "all";

  const updateParams = useCallback(
    (updates: Record<string, string | null>) => {
      const params = new URLSearchParams(searchParams.toString());
      for (const [key, value] of Object.entries(updates)) {
        if (value === null || value === "any" || value === "all") {
          params.delete(key);
        } else {
          params.set(key, value);
        }
      }
      const qs = params.toString();
      router.push(qs ? `?${qs}` : "?");
    },
    [router, searchParams]
  );

  const handleDifficulty = (value: string) => {
    if (!value) return; // toggle-group can fire empty when clicking active item
    updateParams({ difficulty: value as DifficultyBucket });
  };

  const handleStatus = (value: string) => {
    if (!value) return;
    updateParams({ status: value as StatusFilter });
  };

  return (
    <div className="flex flex-wrap items-center gap-4">
      {/* Status filter */}
      <div className="flex items-center gap-2">
        <span className="text-[12px] font-medium text-[var(--text-secondary)]">Status</span>
        <ToggleGroup
          type="single"
          size="sm"
          variant="outline"
          value={currentStatus}
          onValueChange={handleStatus}
        >
          {STATUS_OPTIONS.map((s) => (
            <ToggleGroupItem key={s} value={s}>
              {statusToLabel(s)}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      </div>

      {/* Difficulty filter */}
      <div className="flex items-center gap-2">
        <span className="text-[12px] font-medium text-[var(--text-secondary)]">Difficulty</span>
        <ToggleGroup
          type="single"
          size="sm"
          variant="outline"
          value={currentDifficulty}
          onValueChange={handleDifficulty}
        >
          {DIFFICULTY_OPTIONS.map((d) => (
            <ToggleGroupItem key={d} value={d}>
              {difficultyToLabel(d)}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      </div>

      {/* TODO: Topic filter — deferred until topic column added to GradedUpload */}
    </div>
  );
}
