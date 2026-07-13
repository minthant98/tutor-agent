"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import { IconButton } from "@/components/ui/icon-button";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { useKeyboardShortcut } from "@/hooks/use-keyboard-shortcut";

interface ExitSessionButtonProps {
  className?: string;
}

/**
 * ExitSessionButton — small IconButton (Ghost) in the top-right of SessionShell.
 *
 * - Click opens a confirm dialog.
 * - ESC key (via useKeyboardShortcut) also opens the confirm dialog.
 * - Confirm → navigate to "/" (dashboard). The actual autosave is Task 14.
 * - Cancel → close dialog, stay in session.
 */
export function ExitSessionButton({ className }: ExitSessionButtonProps) {
  const [open, setOpen] = useState(false);
  const router = useRouter();

  const openDialog = useCallback(() => setOpen(true), []);

  // ESC opens the confirm dialog (not the browser default close)
  useKeyboardShortcut("Escape", openDialog, { ignoreInInput: false });

  function handleConfirm() {
    setOpen(false);
    router.push("/");
  }

  return (
    <>
      <IconButton
        variant="ghost"
        aria-label="Exit session"
        onClick={openDialog}
        className={cn("h-8 w-8", className)}
      >
        <X className="h-4 w-4" aria-hidden />
      </IconButton>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Exit this session?</DialogTitle>
            <DialogDescription>
              Your progress is saved. You can resume from the dashboard.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="mt-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={handleConfirm}
            >
              Exit
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
