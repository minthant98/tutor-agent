"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { AccountOut } from "@/lib/types";
import { accountApi } from "@/lib/api/account";

// Section components
import { ProfileSection } from "./profile-section-v3";
import { SubjectsSection } from "./subjects-section";
import { NotificationsSection } from "./notifications-section";
import { ThemeSection } from "./theme-section";
import { ShortcutsSection } from "./shortcuts-section";
import { FeedbackSection } from "./feedback-section";
import { SignOutSection } from "./sign-out-section";

type SectionId =
  | "profile"
  | "subjects"
  | "notifications"
  | "theme"
  | "keyboard-shortcuts"
  | "feedback"
  | "sign-out";

interface NavItem {
  id: SectionId;
  label: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: "profile", label: "Profile" },
  { id: "subjects", label: "Subjects" },
  { id: "notifications", label: "Notifications" },
  { id: "theme", label: "Theme" },
  { id: "keyboard-shortcuts", label: "Keyboard Shortcuts" },
  { id: "feedback", label: "Feedback" },
  { id: "sign-out", label: "Sign Out" },
];

export function AccountShell() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [data, setData] = useState<AccountOut | null>(null);
  const [loading, setLoading] = useState(true);

  const sectionParam = searchParams.get("section") as SectionId | null;
  const activeSection: SectionId =
    sectionParam && NAV_ITEMS.some((n) => n.id === sectionParam)
      ? sectionParam
      : "profile";

  useEffect(() => {
    accountApi
      .get()
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  function navigate(id: SectionId) {
    const params = new URLSearchParams(searchParams.toString());
    params.set("section", id);
    router.push(`?${params.toString()}`);
  }

  return (
    <div className="flex min-h-screen">
      {/* ── Left rail nav ──────────────────────────────────────────── */}
      <nav
        aria-label="Account sections"
        className="w-[240px] shrink-0 border-r border-[var(--border-subtle)] bg-[var(--surface-1)] pt-8"
      >
        <ul className="flex flex-col">
          {NAV_ITEMS.map(({ id, label }) => {
            const isActive = activeSection === id;
            return (
              <li key={id}>
                <a
                  href={`?section=${id}`}
                  onClick={(e) => {
                    e.preventDefault();
                    navigate(id);
                  }}
                  className={[
                    "flex items-center px-5 py-2.5 text-[14px] font-medium transition-colors duration-fast ease-standard",
                    isActive
                      ? "bg-[var(--surface-2)] text-[var(--text-primary)] border-l-2 border-[var(--primary)] -ml-0.5 pl-[calc(1.25rem+2px)]"
                      : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-2)]/50",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  aria-current={isActive ? "page" : undefined}
                >
                  {label}
                </a>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* ── Right pane ─────────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto px-10 py-10">
        <div className="mx-auto max-w-[720px]">
          {loading ? (
            <p className="text-[var(--text-secondary)] text-sm">Loading…</p>
          ) : (
            <SectionContent
              section={activeSection}
              data={data}
              onDataRefresh={() => accountApi.get().then(setData)}
            />
          )}
        </div>
      </main>
    </div>
  );
}

function SectionContent({
  section,
  data,
  onDataRefresh,
}: {
  section: SectionId;
  data: AccountOut | null;
  onDataRefresh: () => void;
}) {
  switch (section) {
    case "profile":
      return data ? (
        <ProfileSection profile={data.profile} billing={data.billing} />
      ) : null;
    case "subjects":
      return data ? (
        <SubjectsSection
          subjects={data.subjects}
          onRefresh={onDataRefresh}
        />
      ) : null;
    case "notifications":
      return <NotificationsSection />;
    case "theme":
      return <ThemeSection />;
    case "keyboard-shortcuts":
      return <ShortcutsSection />;
    case "feedback":
      return <FeedbackSection />;
    case "sign-out":
      return <SignOutSection />;
    default:
      return null;
  }
}
