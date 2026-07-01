"use client";
import { useState } from "react";
import { accountApi } from "@/lib/api/account";
import type { ProfileOut } from "@/lib/types";

export function ProfileSection({ profile }: { profile: ProfileOut }) {
  const [name, setName] = useState(profile.name);

  return (
    <div className="space-y-3">
      <label className="block text-sm">
        Name
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          onBlur={() => accountApi.patchProfile({ name })}
          className="mt-1 w-full rounded-md border border-[var(--border)] px-3 py-2"
        />
      </label>
      <p className="text-sm text-[var(--text-secondary)]">
        Email: {profile.email}
        <button
          onClick={() => alert("Contact support to change your email")}
          className="ml-2 text-[var(--blue)]"
        >
          Change
        </button>
      </p>
    </div>
  );
}
