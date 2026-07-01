"use client";
import { apiFetch } from "@/lib/api";
import type { BillingOut } from "@/lib/types";

export function BillingSection({ billing }: { billing: BillingOut }) {
  const upgrade = async () => {
    const { url } = await apiFetch<{ url: string }>("/billing/checkout", {
      method: "POST",
      body: JSON.stringify({}),
    });
    window.location.href = url;
  };

  const portal = async () => {
    const { url } = await apiFetch<{ url: string }>("/billing/portal", {
      method: "POST",
    });
    window.location.href = url;
  };

  return (
    <div className="rounded-lg border border-[var(--border)] bg-white p-4">
      <p className="mb-3">
        Current Plan:{" "}
        <span className="font-semibold">
          {billing.tier === "free" ? "Free" : "Pro"}
        </span>
      </p>
      {billing.tier === "free" ? (
        <>
          <div className="grid gap-3 sm:grid-cols-2">
            <Benefits
              title="Includes"
              items={["AI coaching", "Practice questions", "Diagnostic"]}
            />
            <Benefits
              title="Unlock with Pro"
              items={[
                "Unlimited marking",
                "Past papers",
                "Advanced analytics",
              ]}
            />
          </div>
          <button
            onClick={upgrade}
            className="mt-4 rounded-lg bg-[var(--blue)] px-4 py-2 text-white"
          >
            Upgrade to Pro
          </button>
        </>
      ) : (
        <button
          onClick={portal}
          className="rounded-lg border border-[var(--border)] px-4 py-2"
        >
          Manage subscription
        </button>
      )}
    </div>
  );
}

function Benefits({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <h4 className="mb-1 text-sm font-semibold">{title}</h4>
      <ul className="space-y-1 text-sm">
        {items.map((i) => (
          <li key={i}>&#10003; {i}</li>
        ))}
      </ul>
    </div>
  );
}
