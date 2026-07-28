import type { AlexMessage as AlexMessageShape } from "@/hooks/use-alex-session";
import { cn } from "@/lib/utils";

interface Props {
  message: AlexMessageShape;
}

/**
 * AlexMessage — renders a single chat bubble for the Alex drawer.
 *
 * User messages: right-aligned, primary surface.
 * Assistant messages: left-aligned, surface-1 with a subtle left border.
 */
export function AlexMessage({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex w-full",
        isUser ? "justify-end" : "justify-start"
      )}
      data-testid={`alex-message-${message.role}`}
    >
      <div
        className={cn(
          "max-w-[85%] rounded-[8px] px-3 py-2 text-[14px] leading-relaxed",
          isUser
            ? "bg-[var(--primary)] text-white"
            : "bg-[var(--surface-1)] text-[var(--text-primary)] border-l-2 border-[var(--border-subtle)]"
        )}
      >
        {message.content || (
          <span className="opacity-50 animate-pulse">·</span>
        )}
      </div>
    </div>
  );
}
