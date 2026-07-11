"use client";
import { useEffect, useState } from "react";
import { getToken } from "@/lib/auth";

export interface ActiveSessionProgress {
  current_question?: number;
  total_questions?: number;
  minutes_remaining?: number;
}

export interface SidebarActiveSession {
  session_id: string;
  subject: string;
  topic: string | null;
  session_type: string;
  progress: ActiveSessionProgress;
}

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

/**
 * Fetches the current in-progress session from the backend.
 * Returns null when there is no active session or the user is not authenticated.
 * Persists across browser close — the backend returns any open session (ended_at IS NULL).
 */
export function useActiveSession(): SidebarActiveSession | null {
  const [session, setSession] = useState<SidebarActiveSession | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) return;

    fetch(`${API}/sessions/active`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (res) => {
        if (!res.ok) return null;
        return res.json() as Promise<SidebarActiveSession | null>;
      })
      .then((data) => {
        // Only set if the response has the sidebar fields (session_type + progress)
        if (data && data.session_type && data.progress) {
          setSession(data);
        } else {
          setSession(null);
        }
      })
      .catch(() => {
        setSession(null);
      });
  }, []);

  return session;
}
