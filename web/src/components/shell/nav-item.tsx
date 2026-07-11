"use client";
import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

interface NavItemProps {
  href: string;
  label: string;
  icon: LucideIcon;
  shortcut: string;
  active: boolean;
  collapsed?: boolean;
}

export function NavItem({ href, label, icon: Icon, shortcut, active, collapsed }: NavItemProps) {
  const link = (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={cn(
        "group relative flex items-center gap-3 rounded-input px-3 py-2 text-14 font-sans transition-colors duration-fast",
        "text-[var(--text-secondary)] hover:bg-[var(--surface-2)] hover:text-[var(--text-primary)]",
        active && [
          "bg-[var(--surface-2)] text-[var(--text-primary)]",
          // 2px indigo left inset accent via before: pseudo-element
          "before:absolute before:left-0 before:top-1 before:bottom-1 before:w-[2px] before:rounded-full before:bg-[var(--primary)]",
        ],
        collapsed ? "justify-center px-0" : ""
      )}
      title={collapsed ? `${label} (${shortcut})` : undefined}
    >
      <Icon
        className={cn(
          "h-4 w-4 shrink-0 transition-colors duration-fast",
          active ? "text-[var(--primary)]" : "text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]"
        )}
        aria-hidden
      />
      {!collapsed && (
        <span className="flex-1 leading-none">{label}</span>
      )}
      {!collapsed && (
        <span
          className="ml-auto text-11 text-[var(--text-muted)] tabular-nums"
          aria-hidden
        >
          {shortcut}
        </span>
      )}
    </Link>
  );

  if (collapsed) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>{link}</TooltipTrigger>
        <TooltipContent side="right">
          {label} <span className="text-[var(--text-muted)]">{shortcut}</span>
        </TooltipContent>
      </Tooltip>
    );
  }

  return link;
}
