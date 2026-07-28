"use client";
import { useEffect, useState } from "react";
import { practiceApi } from "@/lib/api/practice";
import type { PracticeLandingData } from "@/lib/api/practice";

interface UsePracticeNarrationResult {
  data: PracticeLandingData | null;
  isLoading: boolean;
  error: Error | null;
}

export function usePracticeNarration(subject: string): UsePracticeNarrationResult {
  const [data, setData] = useState<PracticeLandingData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    practiceApi
      .getLandingV3(subject)
      .then((payload) => {
        if (!cancelled) {
          setData(payload);
          setIsLoading(false);
        }
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setError(err);
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [subject]);

  return { data, isLoading, error };
}
