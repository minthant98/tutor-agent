"use client";

import { Button } from "@/components/ui/button";
import { useKeyboardShortcut } from "@/hooks/use-keyboard-shortcut";

interface ActionBarProps {
  left?: { label: string; onClick: () => void };
  primary: { label: string; onClick: () => void; shortcut?: string };
  right?: { label: string; onClick: () => void };
}

export function ActionBar({ left, primary, right }: ActionBarProps) {
  useKeyboardShortcut("Enter", primary.onClick);

  return (
    <div className="h-[72px] sticky bottom-0 bg-surface-0 border-t border-border-subtle px-6 grid grid-cols-3 items-center">
      <div data-slot="left" className="justify-self-start">
        {left ? (
          <Button variant="ghost" onClick={left.onClick}>
            {left.label}
          </Button>
        ) : (
          <div />
        )}
      </div>

      <div data-slot="center" className="justify-self-center">
        <Button variant="primary" size="lg" onClick={primary.onClick}>
          {primary.label}
          {primary.shortcut && (
            <span className="ml-2 font-mono text-[11px] opacity-70">
              {primary.shortcut}
            </span>
          )}
        </Button>
      </div>

      <div data-slot="right" className="justify-self-end">
        {right ? (
          <Button variant="ghost" onClick={right.onClick}>
            {right.label}
          </Button>
        ) : (
          <div />
        )}
      </div>
    </div>
  );
}
