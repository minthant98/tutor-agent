"use client";
import { Search, UserCircle2 } from "lucide-react";
import Link from "next/link";
import { Breadcrumb } from "./breadcrumb";
import { SubjectSwitcher } from "./subject-switcher";
import { AskAlexButton } from "./ask-alex-button";
import { IconButton } from "@/components/ui/icon-button";

/**
 * TopBar — sticky desktop/tablet/mobile shell header.
 *
 * Heights: 48px mobile / 52px tablet / 56px desktop (Tailwind responsive).
 * Left  : breadcrumb (two levels max, derived from pathname)
 * Right : SubjectSwitcher · AskAlexButton · Search · ⌘K chip · Avatar (mobile only)
 *
 * NOTE: Avatar is intentionally mobile-only (md:hidden).
 * The desktop sidebar bottom section contains the avatar; duplication is banned.
 */
export function TopBar() {
  function handleSearchClick() {
    window.dispatchEvent(new CustomEvent("stride:open-cmdk"));
  }

  return (
    <header
      role="banner"
      data-topbar
      className={[
        // Responsive height
        "h-[48px] md:h-[52px] lg:h-[56px]",
        // Sticky below nothing (top of viewport)
        "sticky top-0 z-20",
        // Visual
        "flex items-center justify-between px-4",
        "border-b border-[var(--border-subtle)] bg-[var(--surface-0)]",
      ].join(" ")}
    >
      {/* ── Left: breadcrumb ── */}
      <Breadcrumb />

      {/* ── Right: actions ── */}
      <div className="flex items-center gap-1">
        {/* Subject switcher — reads label from hook, never hardcoded */}
        <SubjectSwitcher />

        {/* Ask Alex — dispatches stride:open-alex-drawer */}
        <AskAlexButton />

        {/* Search icon — dispatches stride:open-cmdk */}
        <IconButton
          variant="ghost"
          aria-label="Search"
          onClick={handleSearchClick}
        >
          <Search className="h-4 w-4" aria-hidden />
        </IconButton>

        {/* ⌘K hint chip — desktop only (lg+) */}
        <span
          className="hidden lg:inline-flex items-center px-1.5 py-0.5 rounded border border-[var(--border-subtle)] text-[var(--text-muted)] font-mono text-[12px] select-none"
          aria-hidden
        >
          ⌘K
        </span>

        {/* Avatar — mobile only (hidden on md+); desktop has avatar in sidebar */}
        <Link
          href="/account"
          data-testid="topbar-avatar"
          className="md:hidden flex items-center justify-center rounded-full w-8 h-8 text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors duration-fast ml-1"
          aria-label="Account"
        >
          <UserCircle2 className="h-6 w-6" aria-hidden />
        </Link>
      </div>
    </header>
  );
}
