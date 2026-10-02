"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { api, decodeRole, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [orgName, setOrgName] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const { access_token } = await api<{ access_token: string }>("/auth/dev-login", {
        method: "POST",
        body: JSON.stringify({ email, org_name: orgName || null }),
      });
      setToken(access_token);
      router.push(decodeRole(access_token) === "member" ? "/member" : "/admin");
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <main style={{ maxWidth: 400, margin: "10vh auto" }}>
      <h2>Sign in</h2>
      <div className="card">
        <button disabled style={{ width: "100%" }} title="Available once Reddit API access is approved">
          Continue with Reddit (coming soon)
        </button>
        <p className="muted">Development login until Reddit OAuth is enabled:</p>
        <form onSubmit={submit}>
          <label htmlFor="email">Email</label>
          <input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          <label htmlFor="org">Organization name (new signups only)</label>
          <input id="org" value={orgName} onChange={(e) => setOrgName(e.target.value)} />
          {error && <p className="error">{error}</p>}
          <button className="primary" type="submit" style={{ marginTop: 16, width: "100%" }}>
            Sign in
          </button>
        </form>
      </div>
    </main>
  );
}
