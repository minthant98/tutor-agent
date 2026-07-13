"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

export interface ObservationItem {
  id: string;
  text: string;
  computed_at: string;
}

interface UseObservationsResult {
  observations: ObservationItem[];
  isLoading: boolean;
  error: Error | null;
}

/**
 * Fetches this week's Alex observations for a given subject.
 * Returns an empty array on error or while loading — the component
 * renders nothing in those cases.
 */
export function useObservations(subject: string): UseObservationsResult {
  const [observations, setObservations] = useState<ObservationItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    apiFetch<ObservationItem[]>(
      `/observations/current-week?subject=${encodeURIComponent(subject)}`
    )
      .then((data) => {
        if (!cancelled) {
          setObservations(data);
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

  return { observations, isLoading, error };
}
