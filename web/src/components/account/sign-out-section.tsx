"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { signOut } from "@/lib/auth";

export function SignOutSection() {
  const [open, setOpen] = useState(false);
  const router = useRouter();

  async function handleConfirm() {
    await signOut();
    setOpen(false);
    router.push("/login");
  }

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-[var(--text-primary)]">
        Sign Out
      </h2>

      <p className="text-[14px] text-[var(--text-secondary)]">
        You will be signed out of your Stride account on this device.
      </p>

      <Button variant="destructive" size="md" onClick={() => setOpen(true)}>
        Sign out
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Sign out?</DialogTitle>
          </DialogHeader>
          <p className="text-[14px] text-[var(--text-secondary)] mt-2">
            You will be returned to the login page. Your progress is always
            saved.
          </p>
          <DialogFooter className="mt-4">
            <Button variant="secondary" size="sm" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" size="sm" onClick={handleConfirm}>
              Sign out
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
