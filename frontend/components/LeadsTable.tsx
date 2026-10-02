"use client";

import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { Lead } from "@/lib/types";

export default function LeadsTable({ canClaim = false }: { canClaim?: boolean }) {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => api<Lead[]>("/leads").then(setLeads), []);

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, [load]);

  async function claim(id: string) {
    try {
      await api(`/leads/${id}/claim`, { method: "POST" });
      await load();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  if (!leads.length) return <p className="muted">No leads yet.</p>;

  return (
    <div className="card" style={{ overflowX: "auto" }}>
      {error && <p className="error">{error}</p>}
      <table>
        <thead>
          <tr>
            <th>Post</th>
            <th>Subreddit</th>
            <th>Intent</th>
            <th>Status</th>
            {canClaim && <th />}
          </tr>
        </thead>
        <tbody>
          {leads.map((lead) => (
            <tr key={lead.id}>
              <td>
                <a href={lead.permalink} target="_blank" rel="noreferrer">
                  {lead.title}
                </a>
              </td>
              <td>r/{lead.subreddit}</td>
              <td>{lead.intent_score?.toFixed(2) ?? "-"}</td>
              <td>
                <span className="badge">{lead.status}</span>
              </td>
              {canClaim && (
                <td>{lead.status === "qualified" && <button onClick={() => claim(lead.id)}>Claim</button>}</td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
