"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { TenantConfig } from "@/lib/types";

const listFields = ["subreddits", "keywords", "personas"] as const;

export default function ConfigPage() {
  const [config, setConfig] = useState<TenantConfig | null>(null);
  const [description, setDescription] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    api<TenantConfig>("/config").then(setConfig).catch((e) => setMessage(e.message));
  }, []);

  if (!config) return <p className="muted">{message ?? "Loading…"}</p>;

  const update = <K extends keyof TenantConfig>(key: K, value: TenantConfig[K]) => setConfig({ ...config, [key]: value });

  async function interpret() {
    const s = await api<Pick<TenantConfig, "niche" | "subreddits" | "keywords" | "personas">>("/config/interpret", {
      method: "POST",
      body: JSON.stringify({ description }),
    });
    setConfig({ ...config!, ...s, product_description: description });
    setMessage("Suggestion applied below. Review it, then save.");
  }

  async function save() {
    const saved = await api<TenantConfig>("/config", { method: "PUT", body: JSON.stringify(config) });
    setConfig(saved);
    setMessage("Saved.");
  }

  return (
    <>
      <h2>Niche configuration</h2>
      <div className="card">
        <label htmlFor="describe">Describe what you sell</label>
        <textarea id="describe" placeholder="I sell refurbished mobile phones" value={description} onChange={(e) => setDescription(e.target.value)} />
        <button style={{ marginTop: 10 }} onClick={interpret} disabled={!description}>
          Suggest configuration
        </button>
      </div>

      <div className="card">
        <label htmlFor="niche">Niche</label>
        <input id="niche" value={config.niche} onChange={(e) => update("niche", e.target.value)} />
        <label htmlFor="product">Product description</label>
        <textarea id="product" value={config.product_description} onChange={(e) => update("product_description", e.target.value)} />
        {listFields.map((field) => (
          <div key={field}>
            <label htmlFor={field}>{field} (one per line)</label>
            <textarea
              id={field}
              value={config[field].join("\n")}
              onChange={(e) => update(field, e.target.value.split("\n").map((s) => s.trim()).filter(Boolean))}
            />
          </div>
        ))}
        <label htmlFor="tone">Tone</label>
        <input id="tone" value={config.tone} onChange={(e) => update("tone", e.target.value)} />
        <label htmlFor="strategy">Lead distribution</label>
        <select
          id="strategy"
          value={config.distribution_strategy}
          onChange={(e) => update("distribution_strategy", e.target.value as TenantConfig["distribution_strategy"])}
        >
          <option value="round_robin">Round robin</option>
          <option value="least_recently_active">Least recently active</option>
          <option value="manual_claim">Manual claim</option>
        </select>
        <label htmlFor="threshold">Intent threshold (0–1)</label>
        <input id="threshold" type="number" step="0.05" min="0" max="1" value={config.intent_threshold} onChange={(e) => update("intent_threshold", Number(e.target.value))} />
        <label htmlFor="interval">Poll interval (minutes)</label>
        <input id="interval" type="number" min="5" value={config.poll_interval_minutes} onChange={(e) => update("poll_interval_minutes", Number(e.target.value))} />
        <label className="row" style={{ color: "var(--text)" }}>
          <input type="checkbox" style={{ width: "auto" }} checked={config.is_live} onChange={(e) => update("is_live", e.target.checked)} />
          Live (scheduled polling enabled)
        </label>
        <button className="primary" style={{ marginTop: 16 }} onClick={save}>
          Save
        </button>
        {message && <p className="muted">{message}</p>}
      </div>
    </>
  );
}
