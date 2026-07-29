"use client";
import { useEffect, useState, Suspense } from "react";
import { useRouter } from "next/navigation";
import { accountApi } from "@/lib/api/account";
import { useFeatureFlag } from "@/lib/feature-flags";
import { SubjectCard } from "@/components/account/subject-card";
import { PreferencesSection } from "@/components/account/preferences-section";
import { BillingSection } from "@/components/account/billing-section";
import { ProfileSection } from "@/components/account/profile-section";
import { DangerZone } from "@/components/account/danger-zone";
import { AccountShell } from "@/components/account/account-shell";
import type { AccountOut } from "@/lib/types";

export default function AccountPage() {
  const v3 = useFeatureFlag("account_v3", true);
  const v2 = useFeatureFlag("account_v2", true);
  const router = useRouter();
  const [data, setData] = useState<AccountOut | null>(null);

  useEffect(() => {
    // v3 shell handles its own data fetching
    if (v3) return;

    if (!v2) {
      router.replace("/dashboard");
      return;
    }
    accountApi.get().then(setData);
  }, [v2, v3, router]);

  // ── v3 two-pane shell ────────────────────────────────────────────────────
  if (v3) {
    return (
      <Suspense fallback={<p className="p-10 text-sm text-[var(--text-secondary)]">Loading…</p>}>
        <AccountShell />
      </Suspense>
    );
  }

  // ── v2 legacy layout ─────────────────────────────────────────────────────
  if (!v2 || !data) return <p>Loading…</p>;

  return (
    <div className="space-y-10">
      <Section id="academic" title="Academic Setup">
        {data.subjects.map((s) => (
          <SubjectCard
            key={s.id}
            subject={s}
            onUpdated={() => accountApi.get().then(setData)}
          />
        ))}
        <button
          disabled
          className="mt-2 rounded-lg border border-dashed border-[var(--border)] px-4 py-2 text-sm text-[var(--text-secondary)]"
          title="Coming soon"
        >
          + Add subject (Coming soon)
        </button>
      </Section>

      <Section id="learning-preferences" title="Learning Preferences">
        <p className="mb-3 text-sm text-[var(--text-secondary)]">
          These preferences personalise how Stride explains concepts. They don&apos;t change what you learn.
        </p>
        <PreferencesSection initial={data.preferences} />
      </Section>

      <Section id="profile" title="Profile">
        <ProfileSection profile={data.profile} />
      </Section>

      <Section id="billing" title="Billing">
        <BillingSection billing={data.billing} />
      </Section>

      <Section id="danger-zone" title="Danger Zone">
        <DangerZone />
      </Section>
    </div>
  );
}

function Section({
  id,
  title,
  children,
}: {
  id: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id}>
      <h2 className="mb-4 text-lg font-semibold">{title}</h2>
      {children}
    </section>
  );
}
