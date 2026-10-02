"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { ApprovalApplication, ApprovalGuide, CheckResult } from "@/lib/types";

const STATUS_ICON = { pass: "✓", warn: "!", fail: "✕" } as const;
const STATUS_COLOR = { pass: "var(--ok)", warn: "#b7791f", fail: "var(--danger)" } as const;

type TextField = "app_name" | "company_name" | "contact_email" | "website_url" | "privacy_policy_url" | "reddit_username";

const TEXT_FIELDS: [TextField, string][] = [
  ["app_name", "App / project name"],
  ["company_name", "Company or your name"],
  ["contact_email", "Contact email"],
  ["reddit_username", "Reddit username you'll apply from (no u/)"],
  ["website_url", "Website or repo URL (https)"],
  ["privacy_policy_url", "Privacy policy URL (https)"],
];

export default function ApprovalPage() {
  const [guide, setGuide] = useState<ApprovalGuide | null>(null);
  const [form, setForm] = useState<ApprovalApplication | null>(null);
  const [check, setCheck] = useState<CheckResult | null>(null);
  const [checking, setChecking] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  function apply(g: ApprovalGuide) {
    setGuide(g);
    setForm(g.application);
    setCheck(g.check);
  }

  useEffect(() => {
    api<ApprovalGuide>("/approval").then(apply).catch((e) => setMessage(e.message));
  }, []);

  if (!guide || !form || !check) return <p className="muted">{message ?? "Loading…"}</p>;

  const set = <K extends keyof ApprovalApplication>(key: K, value: ApprovalApplication[K]) => setForm({ ...form, [key]: value });

  async function save(next: ApprovalApplication = form!) {
    const g = await api<ApprovalGuide>("/approval", { method: "PUT", body: JSON.stringify(next) });
    apply(g);
    return g;
  }

  async function checkNow() {
    setChecking(true);
    setMessage(null);
    try {
      await save();
      setCheck(await api<CheckResult>("/approval/check", { method: "POST" }));
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setChecking(false);
    }
  }

  async function toggleStep(id: string) {
    const steps_done = form!.steps_done.includes(id) ? form!.steps_done.filter((s) => s !== id) : [...form!.steps_done, id];
    await save({ ...form!, steps_done });
  }

  async function copyRequest() {
    await navigator.clipboard.writeText(guide!.request_text);
    setMessage("Request text copied. Paste it into Reddit's request form.");
  }

  const done = form.steps_done.length;

  return (
    <>
      <h2>Reddit API approval</h2>
      <p className="muted">
        Reddit approves every app manually under its Responsible Builder Policy. Fill this in, click <b>Check now</b>, fix what fails,
        then follow the steps and submit the generated request.
      </p>

      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div>
            <b>Access tier</b>
            <div className="muted">
              {form.is_commercial
                ? "Commercial: needs a paid contract with Reddit. Required before any customer uses the app."
                : "Free (non-commercial): internal development and testing only, with no customers and no revenue."}
            </div>
          </div>
          <select
            value={form.is_commercial ? "commercial" : "free"}
            onChange={(e) => set("is_commercial", e.target.value === "commercial")}
            style={{ width: 200 }}
          >
            <option value="free">Free (dev / testing)</option>
            <option value="commercial">Commercial</option>
          </select>
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Application details</h3>
        {TEXT_FIELDS.map(([key, label]) => (
          <div key={key}>
            <label htmlFor={key}>{label}</label>
            <input id={key} value={form[key]} onChange={(e) => set(key, e.target.value)} />
          </div>
        ))}
        <label htmlFor="age">Reddit account age (days)</label>
        <input id="age" type="number" min={0} value={form.reddit_account_age_days} onChange={(e) => set("reddit_account_age_days", Number(e.target.value))} />
        <label htmlFor="retention">Keep Reddit data for (days)</label>
        <input id="retention" type="number" min={0} value={form.data_retention_days} onChange={(e) => set("data_retention_days", Number(e.target.value))} />
        <div className="row" style={{ marginTop: 16 }}>
          <button className="primary" onClick={checkNow} disabled={checking}>
            {checking ? "Checking…" : "Save & check now"}
          </button>
          {message && <span className="muted">{message}</span>}
        </div>
      </div>

      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h3 style={{ margin: 0 }}>Readiness check</h3>
          <span className="badge" style={{ color: check.ready ? "var(--ok)" : "var(--danger)" }}>
            {check.ready ? "Ready to submit" : "Not ready"} · {check.score}/100
          </span>
        </div>
        <ul style={{ listStyle: "none", padding: 0, margin: "12px 0 0" }}>
          {check.items.map((item) => (
            <li key={item.id} style={{ padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
              <span style={{ color: STATUS_COLOR[item.status], fontWeight: 700, display: "inline-block", width: 20 }}>{STATUS_ICON[item.status]}</span>
              <b>{item.title}</b>
              <div className="muted" style={{ marginLeft: 20 }}>{item.detail}</div>
              {item.fix && <div style={{ marginLeft: 20, fontSize: 13 }}>→ {item.fix}</div>}
            </li>
          ))}
        </ul>
      </div>

      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h3 style={{ margin: 0 }}>Steps</h3>
          <span className="muted">
            {done}/{guide.steps.length} done
          </span>
        </div>
        <ol style={{ paddingLeft: 20 }}>
          {guide.steps.map((step) => (
            <li key={step.id} style={{ margin: "12px 0" }}>
              <label className="row" style={{ color: "var(--text)", margin: 0, fontSize: 15 }}>
                <input type="checkbox" style={{ width: "auto" }} checked={form.steps_done.includes(step.id)} onChange={() => toggleStep(step.id)} />
                <b style={{ textDecoration: form.steps_done.includes(step.id) ? "line-through" : "none" }}>{step.title}</b>
              </label>
              <div className="muted" style={{ marginLeft: 24 }}>{step.body}</div>
              {step.link && (
                <a href={step.link} target="_blank" rel="noreferrer" style={{ marginLeft: 24, fontSize: 13 }}>
                  {step.link_label} ↗
                </a>
              )}
            </li>
          ))}
        </ol>
      </div>

      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h3 style={{ margin: 0 }}>Your request text</h3>
          <button onClick={copyRequest}>Copy</button>
        </div>
        <p className="muted">Generated from your niche config and the details above. Read it and edit anything that isn't accurate before you submit.</p>
        <pre style={{ whiteSpace: "pre-wrap", fontSize: 13, background: "var(--bg)", padding: 12, borderRadius: 6 }}>{guide.request_text}</pre>
      </div>

      <div className="card">
        <label htmlFor="status">Request status</label>
        <select id="status" value={form.status} onChange={(e) => save({ ...form, status: e.target.value as ApprovalApplication["status"] })}>
          <option value="not_started">Not submitted yet</option>
          <option value="submitted">Submitted, waiting</option>
          <option value="approved">Approved</option>
          <option value="denied">Denied</option>
        </select>
        {form.submitted_at && <p className="muted">Submitted {new Date(form.submitted_at).toLocaleDateString()}. Don&apos;t file a duplicate request.</p>}
      </div>
    </>
  );
}
