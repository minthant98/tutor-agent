"use client";
import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";

export function AskAlexButton() {
  function handleClick() {
    window.dispatchEvent(new CustomEvent("stride:open-alex-drawer"));
  }

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={handleClick}
      aria-label="Ask Alex"
    >
      <Sparkles className="h-4 w-4 mr-1.5" aria-hidden />
      Ask Alex
    </Button>
  );
}
