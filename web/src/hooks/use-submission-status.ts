"use client";

import { useEffect, useRef, useState } from "react";
import type { ProcessingStatus, ProcessingKind } from "@/components/marker/processing-states";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

interface Submission {
  id: string;
  status: ProcessingStatus;
  kind?: ProcessingKind;
  [key: string]: unknown;
}

interface SubmissionStatusResult {
  status: ProcessingStatus | null;
  kind?: ProcessingKind;
  error: string | null;
  submission: Submission | null;
}

const TERMINAL_STATUSES: ProcessingStatus[] = ["graded", "error"];
const POLL_INTERVAL_MS = 2000;

export function useSubmissionStatus(id: string | null): SubmissionStatusResult {
  const [result, setResult] = useState<SubmissionStatusResult>({
    status: null,
    kind: undefined,
    error: null,
    submission: null,
  });

  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const stoppedRef = useRef(false);

  useEffect(() => {
    if (!id) return;

    stoppedRef.current = false;

    async function poll() {
      if (stoppedRef.current) return;

      const token =
        typeof window !== "undefined" ? localStorage.getItem("token") : null;

      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;

      try {
        const res = await fetch(`${API}/marker/submissions/${id}`, { headers });

        if (!res.ok) {
          setResult((prev) => ({
            ...prev,
            error: `Request failed: ${res.status}`,
            status: "error",
          }));
          stoppedRef.current = true;
          return;
        }

        const data = (await res.json()) as Submission;
        const status = data.status as ProcessingStatus;
        const kind = data.kind as ProcessingKind | undefined;

        setResult({
          status,
          kind,
          error: null,
          submission: data,
        });

        if (TERMINAL_STATUSES.includes(status)) {
          stoppedRef.current = true;
          return;
        }
      } catch (err) {
        setResult((prev) => ({
          ...prev,
          error: err instanceof Error ? err.message : "Unknown error",
          status: "error",
        }));
        stoppedRef.current = true;
        return;
      }

      if (!stoppedRef.current) {
        timeoutRef.current = setTimeout(poll, POLL_INTERVAL_MS);
      }
    }

    poll();

    return () => {
      stoppedRef.current = true;
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, [id]);

  return result;
}
