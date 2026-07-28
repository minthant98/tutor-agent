"use client";

import { useState } from "react";
import { accountApi } from "@/lib/api/account";
import type { ProfileOut, BillingOut } from "@/lib/types";

interface Props {
  profile: ProfileOut;
  billing: BillingOut;
}

export function ProfileSection({ profile, billing }: Props) {
  const [name, setName] = useState(profile.name);

  const memberSince = new Date().toLocaleDateString("en-GB", {
    year: "numeric",
    month: "long",
  });

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-[var(--text-primary)]">
        Profile
      </h2>

      {/* Name — save on blur */}
      <div className="space-y-1">
        <label
          htmlFor="profile-name"
          className="block text-[13px] font-medium text-[var(--text-secondary)]"
        >
          Name
        </label>
        <input
          id="profile-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onBlur={() => {
            if (name.trim() && name !== profile.name) {
              accountApi.patchProfile({ name: name.trim() });
            }
          }}
          className="w-full rounded-input border border-[var(--border-subtle)] bg-[var(--surface-1)] px-3 py-2 text-[14px] text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--primary)]"
        />
      </div>

      {/* Email — read-only */}
      <div className="space-y-1">
        <label className="block text-[13px] font-medium text-[var(--text-secondary)]">
          Email
        </label>
        <div className="flex items-center gap-3">
          <span className="text-[14px] text-[var(--text-primary)]">
            {profile.email}
          </span>
          <button
            type="button"
            onClick={() => alert("Contact support to change your email.")}
            className="text-[13px] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors duration-fast"
          >
            Change email
          </button>
        </div>
      </div>

      {/* Plan badge */}
      <div className="space-y-1">
        <label className="block text-[13px] font-medium text-[var(--text-secondary)]">
          Plan
        </label>
        <div className="flex items-center gap-3">
          <span className="font-mono text-[13px] font-semibold uppercase tracking-wide text-[var(--text-primary)]">
            {billing.tier}
          </span>
          {billing.tier === "free" && (
            <a
              href="/billing"
              className="text-[13px] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors duration-fast"
            >
              Upgrade to Pro →
            </a>
          )}
        </div>
      </div>

      {/* Member since */}
      <p className="text-[12px] text-[var(--text-secondary)]">
        Member since {memberSince}
      </p>
    </div>
  );
}
