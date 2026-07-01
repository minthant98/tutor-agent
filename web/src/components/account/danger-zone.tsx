"use client";
import { signOut } from "@/lib/auth";
import { useRouter } from "next/navigation";

export function DangerZone() {
  const router = useRouter();

  return (
    <div className="space-y-2 rounded-lg border border-red-200 bg-red-50 p-4">
      <button
        onClick={async () => {
          await signOut();
          router.push("/login");
        }}
        className="rounded-md bg-[var(--blue)] px-4 py-2 text-white"
      >
        Sign out
      </button>
      <button
        onClick={() => alert("Contact support to delete your account")}
        className="block text-sm text-red-600"
      >
        Delete account
      </button>
    </div>
  );
}
