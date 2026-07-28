"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";

export interface MarkSchemePeekProps {
  scheme: string;
  onEventPreReveal: () => void;
}

export function MarkSchemePeek({ scheme, onEventPreReveal }: MarkSchemePeekProps) {
  const [revealed, setRevealed] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);

  if (revealed) {
    return (
      <div className="rounded-card border border-border-subtle bg-surface-1 p-4">
        <div className="mb-2 text-14 font-sans font-medium text-[var(--text-primary)]">
          Mark Scheme
        </div>
        <div className="text-14 whitespace-pre-wrap font-mono text-[var(--color-mark-scheme)]">
          {scheme}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-card border border-border-subtle bg-surface-1 p-4 space-y-3">
      <div className="text-14 font-sans font-medium text-[var(--text-primary)]">
        Mark Scheme
      </div>
      <div className="text-12 text-[var(--text-secondary)]">
        Available after submission
      </div>
      <div className="text-12 text-[var(--text-secondary)]">
        You'll receive the full examiner breakdown once your attempt has been graded.
      </div>
      <Button variant="ghost" size="sm" onClick={() => setConfirmOpen(true)}>
        Reveal anyway
      </Button>

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogTitle>Are you sure?</DialogTitle>
          <DialogDescription>
            Revealing the mark scheme before answering may reduce the value of this
            practice session.
          </DialogDescription>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" size="sm" onClick={() => setConfirmOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                onEventPreReveal();
                setRevealed(true);
                setConfirmOpen(false);
              }}
            >
              Reveal
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
