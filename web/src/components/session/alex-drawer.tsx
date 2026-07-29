"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { AlexMessage } from "./alex-message";
import { useAlexSession } from "@/hooks/use-alex-session";
import { useKeyboardShortcut } from "@/hooks/use-keyboard-shortcut";
import { SendHorizonal } from "lucide-react";

interface Props {
  /** Session ID for context-aware chat. Null when opened outside a session. */
  sessionId: string | null;
}

const SUGGESTION_CHIPS = [
  "Explain the current step",
  "Give me a similar example",
  "What did I miss?",
];

/**
 * AlexDrawer — session-scoped chat panel that slides in from the right.
 *
 * Opens on:
 *   - ⌘/ (primary)
 *   - ⌘J (alias)
 *   - stride:open-alex-drawer CustomEvent (dispatched by "Ask Alex" button)
 *
 * Closes on Esc (Radix handles this).
 *
 * Chat history and unsent draft persist across close/open because the
 * component stays mounted; only `open` toggles.
 */
export function AlexDrawer({ sessionId }: Props) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const { messages, send, isStreaming } = useAlexSession(sessionId ?? "");
  const scrollRef = useRef<HTMLDivElement>(null);
  const inSession = sessionId !== null && sessionId !== "";

  // ── Keyboard shortcuts ──────────────────────────────────────────────────

  const toggle = useCallback(() => setOpen((o) => !o), []);

  useKeyboardShortcut("Cmd+/", toggle, { ignoreInInput: false });
  useKeyboardShortcut("Cmd+J", toggle, { ignoreInInput: false });

  // ── CustomEvent from "Ask Alex" button (Task 4) ─────────────────────────

  useEffect(() => {
    const openDrawer = () => setOpen(true);
    window.addEventListener("stride:open-alex-drawer", openDrawer);
    return () => window.removeEventListener("stride:open-alex-drawer", openDrawer);
  }, []);

  // ── Auto-scroll to bottom on new messages ───────────────────────────────

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // ── Submit handler ──────────────────────────────────────────────────────

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!draft.trim() || isStreaming || !inSession) return;
    send(draft.trim());
    setDraft("");
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      e.currentTarget.form?.requestSubmit();
    }
  }

  function handleChip(chip: string) {
    send(chip);
  }

  // ── Render ──────────────────────────────────────────────────────────────

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetContent
        side="right"
        data-surface="3"
        className="w-[400px] sm:max-w-[400px] p-0 border-l border-[var(--border-subtle)] flex flex-col gap-0"
      >
        {/* Header */}
        <SheetHeader className="px-4 py-3 border-b border-[var(--border-subtle)] flex-none">
          <SheetTitle className="text-[14px] font-semibold text-[var(--text-primary)]">
            Alex
          </SheetTitle>
        </SheetHeader>

        {/* Message list */}
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-3 min-h-0"
        >
          {!inSession ? (
            /* Out-of-session state: honest message + CTA */
            <div className="flex flex-col gap-3 m-auto text-center px-2">
              <p className="text-[14px] text-[var(--text-primary)]">
                Alex answers questions inside a study session.
              </p>
              <p className="text-[12px] text-[var(--text-muted)]">
                Start one to chat with Alex about the question you&apos;re working on.
              </p>
              <Link
                href="/practice"
                onClick={() => setOpen(false)}
                className="inline-block mt-2 text-[13px] font-medium text-[var(--primary)] hover:underline"
              >
                Start a session →
              </Link>
            </div>
          ) : messages.length === 0 ? (
            /* Empty state: suggestion chips */
            <div className="flex flex-col gap-2 mt-auto">
              <p className="text-[12px] text-[var(--text-muted)] text-center pb-2">
                Ask anything about what you&apos;re working on right now.
              </p>
              {SUGGESTION_CHIPS.map((chip) => (
                <button
                  key={chip}
                  onClick={() => handleChip(chip)}
                  className="text-left text-[13px] px-3 py-2 rounded-[6px] border border-[var(--border-subtle)] text-[var(--text-secondary)] hover:bg-[var(--surface-1)] hover:text-[var(--text-primary)] transition-colors duration-fast ease-standard"
                >
                  {chip}
                </button>
              ))}
            </div>
          ) : (
            messages.map((m) => <AlexMessage key={m.id} message={m} />)
          )}
        </div>

        {/* Input footer — hidden when no session is active */}
        {inSession && (
          <form
            onSubmit={handleSubmit}
            className="flex-none border-t border-[var(--border-subtle)] p-3 flex gap-2 items-end"
          >
            <Textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about the current question…"
              rows={1}
              className="flex-1 min-h-[36px] max-h-[120px] resize-none"
              disabled={isStreaming}
            />
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={!draft.trim() || isStreaming}
              aria-label="Send"
            >
              <SendHorizonal className="h-4 w-4" />
            </Button>
          </form>
        )}
      </SheetContent>
    </Sheet>
  );
}
