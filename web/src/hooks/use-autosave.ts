"use client";
import { useEffect, useRef } from "react";
import { getToken } from "@/lib/auth";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

/**
 * Debounced autosave hook — fires a PATCH to /api/v1/sessions/{sessionId}/state
 * after `debounceMs` milliseconds of inactivity on `state`.
 *
 * Uses a ref so the debounced callback always reads the *latest* state,
 * preventing stale-closure bugs when rapid changes occur.
 *
 * Cleanup is called on unmount and whenever deps change, cancelling any
 * pending timer so no stale requests leak out.
 */
export function useAutosave<T>({
  sessionId,
  state,
  debounceMs = 300,
}: {
  sessionId: string;
  state: T;
  debounceMs?: number;
}) {
  const stateRef = useRef<T>(state);
  stateRef.current = state;

  useEffect(() => {
    const t = setTimeout(() => {
      const token = getToken();
      fetch(`${API}/sessions/${sessionId}/state`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(stateRef.current),
      }).catch(() => {
        // Autosave failures are silent — we don't surface these to the user
      });
    }, debounceMs);

    return () => clearTimeout(t);
  }, [state, sessionId, debounceMs]);
}
