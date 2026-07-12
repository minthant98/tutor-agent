"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getToken } from "@/lib/auth";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export interface SearchResult {
  id: string;
  type: "topic" | "submission" | string;
  label: string;
  subtitle?: string;
  href: string;
  topic_id?: string;
}

interface SearchGroups {
  topics: SearchResult[];
  recent: SearchResult[];
  navigate: SearchResult[];
  isLoading: boolean;
  error: string | null;
}

/**
 * Fetches /api/v1/search?q=<query>&context=<context> with 200ms debounce.
 * Splits results by type:
 *   - "topic"      → topics
 *   - "submission" → recent
 *   - everything else stays empty (navigate is static from cmd-k-index.ts)
 */
export function useSearchResults(query: string, context: string | null): SearchGroups {
  const [topics, setTopics] = useState<SearchResult[]>([]);
  const [recent, setRecent] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const fetchResults = useCallback(
    async (q: string, ctx: string | null) => {
      // Cancel any in-flight request
      if (abortRef.current) {
        abortRef.current.abort();
      }
      const controller = new AbortController();
      abortRef.current = controller;

      setIsLoading(true);
      setError(null);

      try {
        const params = new URLSearchParams({ q });
        if (ctx) params.set("context", ctx);

        const token = getToken();
        const res = await fetch(`${API}/search?${params.toString()}`, {
          signal: controller.signal,
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });

        if (!res.ok) {
          throw new Error(`Search failed: ${res.status}`);
        }

        const data: SearchResult[] = await res.json();

        setTopics(data.filter((r) => r.type === "topic"));
        setRecent(data.filter((r) => r.type === "submission"));
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setError((err as Error).message);
          setTopics([]);
          setRecent([]);
        }
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      fetchResults(query, context);
    }, 200);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [query, context, fetchResults]);

  // Cleanup abort controller on unmount
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  return { topics, recent, navigate: [], isLoading, error };
}
