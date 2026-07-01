"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { signOut } from "@/lib/auth";

export function AvatarMenu({ name }: { name: string }) {
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const initial = name?.[0]?.toUpperCase() ?? "?";

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="grid h-8 w-8 place-items-center rounded-full bg-[var(--blue)] text-white text-sm font-semibold"
        aria-label="Account menu"
      >
        {initial}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-44 rounded-md border border-[var(--border)] bg-white py-1 shadow-lg z-50">
          <button
            className="block w-full px-3 py-2 text-left text-sm hover:bg-gray-50"
            onClick={() => {
              setOpen(false);
              router.push("/account");
            }}
          >
            Account
          </button>
          <button
            className="block w-full px-3 py-2 text-left text-sm hover:bg-gray-50"
            onClick={async () => {
              await signOut();
              router.push("/login");
            }}
          >
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}
