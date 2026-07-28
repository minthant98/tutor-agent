"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  GraduationCap,
  ClipboardCheck,
  BookOpen,
  LineChart,
  PanelLeftClose,
  PanelLeftOpen,
  UserCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ContinuePill } from "./continue-pill";
import { NavItem } from "./nav-item";
import { useSidebarState } from "@/hooks/use-sidebar-state";
import { TooltipProvider } from "@/components/ui/tooltip";

const NAV = [
  { href: "/", label: "Home", icon: Home, shortcut: "⌘H" },
  { href: "/practice", label: "Practice", icon: GraduationCap, shortcut: "⌘P" },
  { href: "/mark", label: "Exam Marker", icon: ClipboardCheck, shortcut: "⌘M" },
  { href: "/topics", label: "Topics", icon: BookOpen, shortcut: "⌘T" },
  { href: "/progress", label: "Progress", icon: LineChart, shortcut: "⌘G" },
] as const;

/** Determine if a nav item is active given the current pathname. */
function isActive(href: string, pathname: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(href + "/");
}

interface SidebarProps {
  /** If provided, the sidebar renders inside a Sheet (mobile overlay). */
  inSheet?: boolean;
}

export function Sidebar({ inSheet }: SidebarProps) {
  const pathname = usePathname();
  const { collapsed, toggle } = useSidebarState();

  // When inside Sheet (mobile), always render expanded
  const isCollapsed = inSheet ? false : collapsed;

  return (
    <TooltipProvider delayDuration={400}>
      <aside
        data-sidebar
        className={cn(
          "flex h-full flex-col border-r border-[var(--border-subtle)] bg-[var(--surface-0)]",
          "transition-[width] duration-base ease-standard shrink-0",
          isCollapsed ? "w-16" : "w-60",
          // On mobile, the sidebar is hidden — the Sheet handles visibility
          !inSheet && "hidden md:flex"
        )}
      >
        {/* Logo / branding row */}
        <div
          className={cn(
            "flex h-14 items-center border-b border-[var(--border-subtle)]",
            isCollapsed ? "justify-center px-0" : "px-4"
          )}
        >
          {!isCollapsed && (
            <Link
              href="/"
              className="font-sans text-14 font-semibold tracking-tight text-[var(--text-primary)]"
            >
              Stride
            </Link>
          )}
          {/* Collapse toggle — not shown inside Sheet */}
          {!inSheet && (
            <button
              onClick={toggle}
              aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
              className={cn(
                "rounded-input p-1.5 text-[var(--text-muted)] transition-colors duration-fast",
                "hover:bg-[var(--surface-2)] hover:text-[var(--text-primary)]",
                isCollapsed ? "mx-auto" : "ml-auto"
              )}
            >
              {isCollapsed ? (
                <PanelLeftOpen className="h-4 w-4" aria-hidden />
              ) : (
                <PanelLeftClose className="h-4 w-4" aria-hidden />
              )}
            </button>
          )}
        </div>

        {/* Continue pill — hidden when no active session */}
        <div className="pt-2">
          <ContinuePill collapsed={isCollapsed} />
        </div>

        {/* Primary nav */}
        <nav
          aria-label="Primary"
          className="flex-1 overflow-y-auto px-2 py-1 space-y-0.5"
        >
          {NAV.map((item) => (
            <NavItem
              key={item.href}
              href={item.href}
              label={item.label}
              icon={item.icon}
              shortcut={item.shortcut}
              active={isActive(item.href, pathname ?? "")}
              collapsed={isCollapsed}
            />
          ))}
        </nav>

        {/* Account link at bottom */}
        <div className="border-t border-[var(--border-subtle)] p-2">
          <Link
            href="/account"
            className={cn(
              "group flex items-center gap-2 rounded-input px-3 py-2 text-14 font-sans",
              "text-[var(--text-secondary)] transition-colors duration-fast",
              "hover:bg-[var(--surface-2)] hover:text-[var(--text-primary)]",
              isCollapsed && "justify-center px-0"
            )}
            title={isCollapsed ? "Account" : undefined}
          >
            <UserCircle2
              className="h-5 w-5 shrink-0 text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]"
              aria-hidden
            />
            {!isCollapsed && (
              <span className="leading-none">Account</span>
            )}
          </Link>
        </div>
      </aside>
    </TooltipProvider>
  );
}
