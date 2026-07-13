"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { DashboardV3Payload } from "@/components/dashboard/dashboard-hero";

interface UseDashboardV3Result {
  data: DashboardV3Payload | null;
  isLoading: boolean;
  error: Error | null;
}

export function useDashboardV3(subject: string): UseDashboardV3Result {
  const [data, setData] = useState<DashboardV3Payload | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    apiFetch<DashboardV3Payload>(`/dashboard/v3/${subject}`)
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
