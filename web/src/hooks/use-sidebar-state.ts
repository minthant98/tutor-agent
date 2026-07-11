"use client";
import { useEffect, useState } from "react";

const STORAGE_KEY = "stride_sidebar_collapsed";

/**
 * Persists sidebar collapsed state in localStorage.
 * collapsed=true → 64px icon-only mode
 * collapsed=false → 240px expanded mode
 */
export function useSidebarState() {
  const [collapsed, setCollapsed] = useState<boolean>(() => {
    if (typeof window === "undefined") return false;
    try {
      return localStorage.getItem(STORAGE_KEY) === "true";
    } catch {
      return false;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, String(collapsed));
    } catch {
      // ignore
    }
  }, [collapsed]);

  return { collapsed, toggle: () => setCollapsed((c) => !c) };
}
