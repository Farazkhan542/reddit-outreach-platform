"use client";

import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { Lead, Reply } from "@/lib/types";

/** Human review gate: nothing is posted until someone approves it here. */
export default function ReviewQueue() {
  const [replies, setReplies] = useState<Reply[]>([]);
  const [leads, setLeads] = useState<Record<string, Lead>>({});
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [r, l] = await Promise.all([api<Reply[]>("/replies"), api<Lead[]>("/leads?limit=500")]);
    setReplies(r);
    setLeads(Object.fromEntries(l.map((lead) => [lead.id, lead])));
  }, []);

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, [load]);

  async function act(reply: Reply, action: "approve" | "reject") {
    setError(null);
    try {
      const edited = edits[reply.id];
      if (edited !== undefined && edited !== (reply.final_body ?? reply.draft_body)) {
        await api(`/replies/${reply.id}`, { method: "PATCH", body: JSON.stringify({ final_body: edited }) });
      }
      await api(`/replies/${reply.id}/${action}`, { method: "POST" });
      await load();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  if (!replies.length) return <p className="muted">No drafts waiting for review.</p>;

  return (
    <div>
      {error && <p className="error">{error}</p>}
      {replies.map((reply) => {
        const lead = leads[reply.lead_id];
        return (
          <div key={reply.id} className="card">
            {lead && (
              <>
                <div className="row">
                  <span className="badge">r/{lead.subreddit}</span>
                  <span className="badge">intent {lead.intent_score?.toFixed(2)}</span>
                  <a href={lead.permalink} target="_blank" rel="noreferrer" className="muted">
                    open post
                  </a>
                </div>
                <h4 style={{ margin: "10px 0 4px" }}>{lead.title}</h4>
                <p className="muted">{lead.body}</p>
              </>
            )}
            <label htmlFor={`draft-${reply.id}`}>Draft {reply.kind}</label>
            <textarea
              id={`draft-${reply.id}`}
              value={edits[reply.id] ?? reply.final_body ?? reply.draft_body}
              onChange={(e) => setEdits({ ...edits, [reply.id]: e.target.value })}
            />
            <div className="row" style={{ marginTop: 10 }}>
              <button className="primary" onClick={() => act(reply, "approve")}>
                Approve &amp; post
              </button>
              <button className="danger" onClick={() => act(reply, "reject")}>
                Reject
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
