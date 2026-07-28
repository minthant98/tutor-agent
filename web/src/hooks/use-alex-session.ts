"use client";

import { useState, useCallback } from "react";
import { getToken } from "@/lib/auth";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export interface AlexMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface UseAlexSessionReturn {
  messages: AlexMessage[];
  send: (text: string) => void;
  isStreaming: boolean;
}

/**
 * useAlexSession — session-scoped state for the Alex drawer.
 *
 * Persists across open/close cycles because the drawer is always mounted;
 * only the Sheet open state toggles.
 *
 * send(text):
 *   1. Optimistically appends the user message.
 *   2. Opens a streaming POST to /api/v1/alex/session/{sessionId}/message.
 *   3. Builds the assistant message token-by-token from SSE delta events.
 *   4. Sets isStreaming=false when "done" event arrives or on error.
 */
export function useAlexSession(sessionId: string): UseAlexSessionReturn {
  const [messages, setMessages] = useState<AlexMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const send = useCallback(
    (text: string) => {
      if (!text.trim() || isStreaming) return;

      const userMsg: AlexMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content: text.trim(),
      };

      const assistantId = `assistant-${Date.now() + 1}`;
      const assistantMsg: AlexMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsStreaming(true);

      const token = getToken();

      fetch(`${API}/alex/session/${sessionId}/message`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ text: text.trim() }),
      })
        .then(async (res) => {
          if (!res.ok || !res.body) {
            throw new Error(`HTTP ${res.status}`);
          }

          const reader = res.body.getReader();
          const decoder = new TextDecoder();
          let buffer = "";

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() ?? "";

            for (const line of lines) {
              if (!line.startsWith("data: ")) continue;
              const raw = line.slice(6).trim();
              try {
                const payload = JSON.parse(raw);
                if (payload.delta) {
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantId
                        ? { ...m, content: m.content + payload.delta }
                        : m
                    )
                  );
                }
                if (payload.done) {
                  setIsStreaming(false);
                  return;
                }
                if (payload.error) {
                  throw new Error(payload.error);
                }
              } catch {
                // non-JSON line — skip
              }
            }
          }
          setIsStreaming(false);
        })
        .catch(() => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content: "Something went wrong — try again.",
                  }
                : m
            )
          );
          setIsStreaming(false);
        });
    },
    [sessionId, isStreaming]
  );

  return { messages, send, isStreaming };
}
