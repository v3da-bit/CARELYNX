"use client";

import { useEffect, useState } from "react";
import { getHealth, type Health } from "@/lib/api";

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((e: Error) => setError(e.message));
  }, []);

  return (
    <section className="mx-auto max-w-6xl px-5 py-12 fade-in">
      <h1 className="text-3xl md:text-4xl font-semibold tracking-tight">Clearer discharge instructions</h1>
      <p className="mt-3 max-w-2xl text-muted">
        Upload discharge documents. CARELYNX shows what they say, where each statement came from, and what needs a
        human to check.
      </p>
      <div className="card mt-8 p-5 text-sm" id="api-status">
        {error && <span className="text-human">API unreachable: {error}</span>}
        {!error && !health && <span className="text-muted pulse-dot">Checking API…</span>}
        {health && (
          <span>
            API <b className={health.status === "ok" ? "text-verified" : "text-review"}>{health.status}</b> · DB{" "}
            {health.database_backend} · inference {health.inference_provider} ({health.inference_hardware_label})
          </span>
        )}
      </div>
    </section>
  );
}
