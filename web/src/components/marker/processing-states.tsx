"use client";

import { useEffect, useRef } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { capture } from "@/lib/analytics";

export type ProcessingStatus = "uploading" | "extracting" | "grading" | "graded" | "error";
export type ProcessingKind = "extraction" | "grading";

export interface ProcessingStatesProps {
  status: ProcessingStatus;
  kind?: ProcessingKind;
  onRetry?: () => void;
}

const PHASE_COPY: Record<Exclude<ProcessingStatus, "graded" | "error">, string> = {
  uploading: "Uploading your photos",
  extracting: "Reading your handwriting",
  grading: "Alex is marking your answer",
};

const ERROR_COPY: Record<ProcessingKind, string> = {
  extraction:
    "Couldn't read that photo clearly — please retake or try typing your answer.",
  grading: "Marking hasn't finished — try again in a moment.",
};

export function ProcessingStates({ status, kind, onRetry }: ProcessingStatesProps) {
  // Fire marker_ocr_failed once when this component shows an extraction error.
  // Using a ref ensures it fires at most once even if the component re-renders.
  const ocrFailedFired = useRef(false);
  useEffect(() => {
    if (status === "error" && kind === "extraction" && !ocrFailedFired.current) {
      ocrFailedFired.current = true;
      capture("marker_ocr_failed", { kind });
    }
  }, [status, kind]);

  if (status === "graded") {
    return null;
  }

  if (status === "error") {
    const copy = kind ? ERROR_COPY[kind] : "Something went wrong. Please try again.";
    return (
      <Card
        role="alert"
        className="flex flex-col gap-4 border-[var(--semantic-danger-text)]/30 bg-[var(--semantic-danger-bg)]"
      >
        <p className="text-sm text-[var(--semantic-danger-text)]">{copy}</p>
        {onRetry && (
          <Button variant="secondary" size="sm" onClick={onRetry}>
            Try again
          </Button>
        )}
      </Card>
    );
  }

  const copy = PHASE_COPY[status];

  return (
    <Card className="flex flex-col gap-4">
      <p className="text-sm font-medium text-[var(--text-primary)]">{copy}</p>
      <div className="flex flex-col gap-2">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-4/5" />
        <Skeleton className="h-4 w-2/3" />
      </div>
    </Card>
  );
}
