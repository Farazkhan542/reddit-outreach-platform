"use client";

import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { Lead, Reply } from "@/lib/types";

/**
 * Human review queue. The app never posts to Reddit: a person approves a draft,
 * copies it, posts it themselves on reddit.com, then marks it as posted here.
 */
export default function ReviewQueue() {
  const [replies, setReplies] = useState<Reply[]>([]);
  const [leads, setLeads] = useState<Record<string, Lead>>({});
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [postedUrls, setPostedUrls] = useState<Record<string, string>>({});
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [r, l] = await Promise.all([api<Reply[]>("/replies"), api<Lead[]>("/leads?limit=500")]);
    setReplies(r);
    setLeads(Object.fromEntries(l.map((lead) => [lead.id, lead])));
  }, []);

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, [load]);

  async function run(fn: () => Promise<unknown>) {
    setError(null);
    setNotice(null);
    try {
      await fn();
      await load();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  const textOf = (reply: Reply) => edits[reply.id] ?? reply.final_body ?? reply.draft_body;

  const approve = (reply: Reply) =>
    run(async () => {
      const text = textOf(reply);
      if (text !== (reply.final_body ?? reply.draft_body)) {
        await api(`/replies/${reply.id}`, { method: "PATCH", body: JSON.stringify({ final_body: text }) });
      }
      await api(`/replies/${reply.id}/approve`, { method: "POST" });
    });

  const reject = (reply: Reply) => run(() => api(`/replies/${reply.id}/reject`, { method: "POST" }));

  async function copyAndOpen(reply: Reply, lead?: Lead) {
    await navigator.clipboard.writeText(textOf(reply));
    if (lead) window.open(lead.permalink, "_blank", "noopener");
    setNotice("Reply copied. Paste it as a comment on Reddit, then come back and mark it as posted.");
  }

  const markPosted = (reply: Reply) =>
    run(() =>
      api(`/replies/${reply.id}/mark-posted`, {
        method: "POST",
        body: JSON.stringify({ posted_url: postedUrls[reply.id] || null }),
      }),
    );

  if (!replies.length) return <p className="muted">{error ?? "Nothing to review or post right now."}</p>;

  return (
    <div>
      {error && <p className="error">{error}</p>}
      {notice && <p className="muted">{notice}</p>}
      {replies.map((reply) => {
        const lead = leads[reply.lead_id];
        const approved = reply.status === "approved";
        return (
          <div key={reply.id} className="card">
            <div className="row">
              <span className="badge">{approved ? "Approved: post it yourself" : "Needs review"}</span>
              {lead && (
                <>
                  <span className="badge">r/{lead.subreddit}</span>
                  <span className="badge">intent {lead.intent_score?.toFixed(2)}</span>
                </>
              )}
            </div>
            {lead && (
              <>
                <h4 style={{ margin: "10px 0 4px" }}>{lead.title}</h4>
                <p className="muted">{lead.body}</p>
              </>
            )}

            <label htmlFor={`draft-${reply.id}`}>{approved ? "Approved reply" : "Draft reply"}</label>
            <textarea
              id={`draft-${reply.id}`}
              value={textOf(reply)}
              readOnly={approved}
              onChange={(e) => setEdits({ ...edits, [reply.id]: e.target.value })}
            />

            {approved ? (
              <>
                <div className="row" style={{ marginTop: 10 }}>
                  <button className="primary" onClick={() => copyAndOpen(reply, lead)}>
                    Copy reply &amp; open post ↗
                  </button>
                </div>
                <label htmlFor={`url-${reply.id}`}>After posting: link to your comment (optional)</label>
                <div className="row">
                  <input
                    id={`url-${reply.id}`}
                    placeholder="https://www.reddit.com/r/…/comments/…"
                    value={postedUrls[reply.id] ?? ""}
                    onChange={(e) => setPostedUrls({ ...postedUrls, [reply.id]: e.target.value })}
                    style={{ flex: 1 }}
                  />
                  <button onClick={() => markPosted(reply)}>Mark as posted</button>
                </div>
              </>
            ) : (
              <div className="row" style={{ marginTop: 10 }}>
                <button className="primary" onClick={() => approve(reply)}>
                  Approve
                </button>
                <button className="danger" onClick={() => reject(reply)}>
                  Reject
                </button>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
