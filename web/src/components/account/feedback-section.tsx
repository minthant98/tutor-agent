"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";

type Status = "idle" | "sending" | "sent" | "error";

export function FeedbackSection() {
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [status, setStatus] = useState<Status>("idle");

  async function handleSend() {
    if (!subject.trim() || !body.trim()) return;
    setStatus("sending");
    try {
      await apiFetch("/feedback", {
        method: "POST",
        body: JSON.stringify({ subject: subject.trim(), body: body.trim() }),
      });
      setStatus("sent");
      setSubject("");
      setBody("");
    } catch {
      setStatus("error");
    }
  }

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-[var(--text-primary)]">
        Feedback
      </h2>

      <p className="text-[14px] text-[var(--text-secondary)]">
        Found a bug, have a suggestion, or just want to say hi? We read every
        message.
      </p>

      <div className="space-y-3">
        <div className="space-y-1">
          <label
            htmlFor="feedback-subject"
            className="block text-[13px] font-medium text-[var(--text-secondary)]"
          >
            Subject
          </label>
          <Input
            id="feedback-subject"
            placeholder="e.g. Session page crashed"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            disabled={status === "sending"}
          />
        </div>

        <div className="space-y-1">
          <label
            htmlFor="feedback-body"
            className="block text-[13px] font-medium text-[var(--text-secondary)]"
          >
            Message
          </label>
          <Textarea
            id="feedback-body"
            placeholder="Describe what happened or what you'd like to see…"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            disabled={status === "sending"}
            rows={5}
          />
        </div>

        <Button
          variant="primary"
          size="md"
          onClick={handleSend}
          disabled={status === "sending" || !subject.trim() || !body.trim()}
        >
          {status === "sending" ? "Sending…" : "Send"}
        </Button>

        {status === "sent" && (
          <p className="text-[13px] text-[var(--semantic-success-text,_#22c55e)]">
            Sent. Thanks.
          </p>
        )}
        {status === "error" && (
          <p className="text-[13px] text-[var(--semantic-danger-text)]">
            Something went wrong — please try again.
          </p>
        )}
      </div>
    </div>
  );
}
