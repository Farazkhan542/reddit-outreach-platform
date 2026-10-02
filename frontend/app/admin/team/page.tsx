"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { User } from "@/lib/types";

export default function TeamPage() {
  const [members, setMembers] = useState<User[]>([]);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"member" | "admin">("member");
  const [error, setError] = useState<string | null>(null);

  const load = () => api<User[]>("/org/members").then(setMembers);

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, []);

  async function invite(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api("/org/members", { method: "POST", body: JSON.stringify({ email, role }) });
      setEmail("");
      await load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <>
      <h2>Team</h2>
      <form className="card row" onSubmit={invite}>
        <input type="email" required placeholder="teammate@company.com" value={email} onChange={(e) => setEmail(e.target.value)} style={{ flex: 1 }} />
        <select value={role} onChange={(e) => setRole(e.target.value as "member" | "admin")} style={{ width: 120 }}>
          <option value="member">Member</option>
          <option value="admin">Admin</option>
        </select>
        <button className="primary" type="submit">
          Invite
        </button>
      </form>
      {error && <p className="error">{error}</p>}
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {members.map((m) => (
              <tr key={m.id}>
                <td>{m.email}</td>
                <td>{m.role}</td>
                <td>{m.is_active ? "active" : "deactivated"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="muted">Each teammate connects their own Reddit account once Reddit OAuth is enabled.</p>
      </div>
    </>
  );
}
