"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { Analytics } from "@/lib/types";

export default function AdminOverview() {
  const [stats, setStats] = useState<Analytics | null>(null);
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const load = () => api<Analytics>("/analytics").then(setStats);

  useEffect(() => {
    load().catch((e) => setMessage(e.message));
  }, []);

  async function runPipeline() {
    setRunning(true);
    setMessage(null);
    try {
      const r = await api<{ scanned: number; qualified: number; drafts: number }>("/pipeline/run", { method: "POST" });
      setMessage(`Scanned ${r.scanned} posts · ${r.qualified} qualified · ${r.drafts} drafts queued for review`);
      await load();
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setRunning(false);
    }
  }

  const tiles: [string, string | number][] = stats
    ? [
        ["Leads found", stats.leads_total],
        ["Qualified", stats.leads_qualified],
        ["Awaiting review", stats.replies_pending],
        ["Replies sent", stats.replies_sent],
        ["Approval rate", stats.approval_rate == null ? "-" : `${Math.round(stats.approval_rate * 100)}%`],
      ]
    : [];

  return (
    <>
      <h2>Overview</h2>
      <div className="stats">
        {tiles.map(([label, value]) => (
          <div key={label} className="card stat">
            <div className="value">{value}</div>
            <div className="label">{label}</div>
          </div>
        ))}
      </div>
      <div className="card">
        <p className="muted">Runs Scout → Classifier → Drafter once now (mock Reddit data until API access is granted).</p>
        <button className="primary" disabled={running} onClick={runPipeline}>
          {running ? "Running…" : "Run pipeline now"}
        </button>
        {message && <p className="muted">{message}</p>}
      </div>
    </>
  );
}
