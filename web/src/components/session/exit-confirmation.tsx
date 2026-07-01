"use client";
import { useRouter } from "next/navigation";

export function ExitConfirmation({ open, onClose, hasProgress }: { open: boolean; onClose: () => void; hasProgress: boolean }) {
  const router = useRouter();
  if (!open) return null;
  const leave = () => router.push("/dashboard");
  if (!hasProgress) { leave(); return null; }
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40">
      <div className="w-full max-w-sm rounded-lg bg-white p-5 shadow-xl">
        <h2 className="text-lg font-semibold">Leave session?</h2>
        <p className="mt-2 text-sm text-[var(--text-secondary)]">Your progress has been saved — you can pick up where you left off from your dashboard.</p>
        <div className="mt-5 flex justify-end gap-2">
          <button onClick={onClose} className="rounded-md border border-[var(--border)] px-4 py-2 text-sm hover:bg-gray-50">Continue</button>
          <button onClick={leave} className="rounded-md bg-[var(--blue)] px-4 py-2 text-sm text-white">Leave session</button>
        </div>
      </div>
    </div>
  );
}
