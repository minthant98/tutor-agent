"use client";
import Link from "next/link";
import Logo from "@/components/Logo";
import { NotificationBell } from "./notification-bell";
import { AvatarMenu } from "./avatar-menu";

export function TopBar({ studentName }: { studentName: string }) {
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-[var(--border)] bg-white px-4">
      <Link href="/dashboard" className="flex items-center gap-2">
        <Logo size="sm" />
      </Link>
      <div className="flex items-center gap-3">
        <NotificationBell />
        <AvatarMenu name={studentName} />
      </div>
    </header>
  );
}
