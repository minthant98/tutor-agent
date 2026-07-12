"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";

import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandShortcut,
} from "@/components/ui/command";
import { useSearchResults } from "@/hooks/use-cmd-k";
import { ACTIONS, ACCOUNT_ITEMS, NAV_ITEMS, type CmdItem } from "@/lib/cmd-k-index";

/**
 * Extract topic_id from pathname patterns:
 *   /topics/<topic_id>
 *   /sessions/<id>?topic=<topic_id>  — handled by URLSearchParams at call site
 *   /mark/<id>?topic=<topic_id>      — handled by URLSearchParams at call site
 */
function extractTopicFromPath(pathname: string): string | null {
  const m = pathname.match(/\/topics\/([^/]+)/);
  return m ? m[1] : null;
}

export function CmdK() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const router = useRouter();
  const pathname = usePathname();
  const context = extractTopicFromPath(pathname);

  const { topics, recent, navigate, isLoading } = useSearchResults(query, context);

  // Keyboard shortcut: ⌘K or Ctrl+K toggles the palette
  useEffect(() => {
    const keyHandler = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    };
    document.addEventListener("keydown", keyHandler);
    return () => document.removeEventListener("keydown", keyHandler);
  }, []);

  // Custom event: stride:open-cmdk (dispatched from TopBar search icon, etc.)
  useEffect(() => {
    const openHandler = () => setOpen(true);
    window.addEventListener("stride:open-cmdk", openHandler);
    return () => window.removeEventListener("stride:open-cmdk", openHandler);
  }, []);

  // Reset query when palette closes
  useEffect(() => {
    if (!open) {
      setQuery("");
    }
  }, [open]);

  function handleSelect(item: CmdItem | { href: string }) {
    if ("href" in item && item.href === "#toggle-theme") {
      // Theme toggle: handled here; future: dispatch a custom event
      document.documentElement.classList.toggle("dark");
    } else {
      router.push(item.href);
    }
    setOpen(false);
  }

  const hasResults =
    !isLoading && (recent.length > 0 || navigate.length > 0 || topics.length > 0);
  const showEmpty = query.length > 0 && !isLoading && !hasResults;

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput
        placeholder="Search or run a command…"
        value={query}
        onValueChange={setQuery}
      />
      <CommandList>
        {/* ── Actions (static, always shown) ─────────────────────── */}
        <CommandGroup heading="Actions">
          {ACTIONS.map((a) => (
            <CommandItem key={a.id} onSelect={() => handleSelect(a)}>
              <span>{a.label}</span>
              {a.shortcut && (
                <CommandShortcut>{a.shortcut}</CommandShortcut>
              )}
            </CommandItem>
          ))}
        </CommandGroup>

        {/* ── Recent submissions (from backend) ───────────────────── */}
        {recent.length > 0 && (
          <CommandGroup heading="Recent">
            {recent.map((r) => (
              <CommandItem key={r.id} onSelect={() => handleSelect(r)}>
                <span className="truncate">{r.label}</span>
                {r.subtitle && (
                  <CommandShortcut>{r.subtitle}</CommandShortcut>
                )}
              </CommandItem>
            ))}
          </CommandGroup>
        )}

        {/* ── Navigate (static nav items) ─────────────────────────── */}
        {NAV_ITEMS.length > 0 && (
          <CommandGroup heading="Navigate">
            {NAV_ITEMS.map((n) => (
              <CommandItem key={n.id} onSelect={() => handleSelect(n)}>
                <span>{n.label}</span>
              </CommandItem>
            ))}
          </CommandGroup>
        )}

        {/* ── Topics (from backend) ───────────────────────────────── */}
        {topics.length > 0 && (
          <CommandGroup heading="Topics">
            {topics.map((t) => (
              <CommandItem key={t.id} onSelect={() => handleSelect(t)}>
                <span>{t.label}</span>
                {t.subtitle && (
                  <CommandShortcut>{t.subtitle}</CommandShortcut>
                )}
              </CommandItem>
            ))}
          </CommandGroup>
        )}

        {/* ── Account (static) ────────────────────────────────────── */}
        <CommandGroup heading="Account">
          {ACCOUNT_ITEMS.map((a) => (
            <CommandItem key={a.id} onSelect={() => handleSelect(a)}>
              <span>{a.label}</span>
            </CommandItem>
          ))}
        </CommandGroup>

        {/* ── Empty state ─────────────────────────────────────────── */}
        {showEmpty && <CommandEmpty>No matches</CommandEmpty>}
      </CommandList>
    </CommandDialog>
  );
}
