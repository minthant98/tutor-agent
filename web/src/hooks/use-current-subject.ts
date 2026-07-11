"use client";
import { useState, useCallback } from "react";

export type Subject = { id: string; label: string };

/**
 * TEMPORARY STUB — localStorage-backed subject selection.
 *
 * This will be replaced by a real implementation backed by
 * `GET /api/v1/subjects` in a later task. The interface is
 * intentionally API-generic so the UI never hardcodes subject strings.
 */

const DEFAULT_SUBJECTS: Subject[] = [
  { id: "pure_mathematics", label: "Pure Mathematics" },
  { id: "statistics", label: "Statistics" },
  { id: "mechanics", label: "Mechanics" },
];

const STORAGE_KEY = "stride_current_subject";

function readFromStorage(): string {
  if (typeof window === "undefined") return DEFAULT_SUBJECTS[0].id;
  return (
    window.localStorage.getItem(STORAGE_KEY) ?? DEFAULT_SUBJECTS[0].id
  );
}

export function useCurrentSubject() {
  const [subject, setSubjectState] = useState<string>(readFromStorage);

  const setSubject = useCallback((id: string) => {
    setSubjectState(id);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, id);
    }
  }, []);

  return {
    subject,
    subjects: DEFAULT_SUBJECTS,
    setSubject,
  };
}
