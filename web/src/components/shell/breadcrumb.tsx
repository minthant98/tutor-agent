"use client";
import { usePathname } from "next/navigation";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Static map of URL segments → display labels.
 * Only used here — never leak raw segment strings into UI.
 */
const SEGMENT_LABELS: Record<string, string> = {
  practice: "Practice",
  mark: "Exam Marker",
  topics: "Topics",
  progress: "Progress",
  account: "Account",
  sessions: "Session",
  plan: "Plan",
  settings: "Settings",
};

function toLabel(segment: string): string {
  return (
    SEGMENT_LABELS[segment] ??
    // Fallback: capitalise first letter, replace hyphens/underscores with spaces
    segment
      .replace(/[-_]/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase())
  );
}

export interface BreadcrumbProps {
  /** Inject pathname directly (used in tests to avoid the Next.js router). */
  pathname?: string;
  className?: string;
}

export function Breadcrumb({ pathname: pathnameOverride, className }: BreadcrumbProps) {
  const routerPathname = usePathname();
  const pathname = pathnameOverride ?? routerPathname ?? "/";

  // Build segments, limiting to a maximum of TWO levels.
  let segments: { label: string; key: string }[];

  if (pathname === "/") {
    segments = [{ label: "Home", key: "home" }];
  } else {
    const parts = pathname.split("/").filter(Boolean);
    // Never render more than two levels.
    const trimmed = parts.slice(0, 2);
    segments = trimmed.map((seg) => ({ label: toLabel(seg), key: seg }));
  }

  return (
    <nav aria-label="Breadcrumb" className={cn("flex items-center gap-1", className)}>
      {segments.map((seg, idx) => (
        <span key={seg.key} className="flex items-center gap-1">
          {idx > 0 && (
            <ChevronRight
              className="h-3.5 w-3.5 text-[var(--text-muted)] shrink-0"
              aria-hidden
            />
          )}
          <span
            className={cn(
              "font-sans text-[14px] leading-none",
              idx === segments.length - 1
                ? "text-[var(--text-primary)] font-medium"
                : "text-[var(--text-secondary)]"
            )}
          >
            {seg.label}
          </span>
        </span>
      ))}
    </nav>
  );
}
