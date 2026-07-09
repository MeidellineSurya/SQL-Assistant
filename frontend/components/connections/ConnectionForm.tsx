"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Connection } from "@/types";

export function ConnectionForm({ onCreated }: { onCreated: (conn: Connection) => void }) {
  const [name, setName] = useState("");
  const [host, setHost] = useState("");
  const [port, setPort] = useState("5432");
  const [databaseName, setDatabaseName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [sslMode, setSslMode] = useState("require");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const conn = await api.createConnection({
        name,
        host,
        port: Number(port),
        database_name: databaseName,
        username,
        password,
        ssl_mode: sslMode,
      });
      onCreated(conn);
      setName("");
      setHost("");
      setPort("5432");
      setDatabaseName("");
      setUsername("");
      setPassword("");
      setSslMode("require");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 rounded-lg border p-4">
      <h2 className="text-sm font-semibold">Add a database connection</h2>

      <div className="grid grid-cols-2 gap-3">
        <Field label="Name">
          <input value={name} onChange={(e) => setName(e.target.value)} required className="input" />
        </Field>
        <Field label="Host">
          <input value={host} onChange={(e) => setHost(e.target.value)} required className="input" />
        </Field>
        <Field label="Port">
          <input
            type="number"
            value={port}
            onChange={(e) => setPort(e.target.value)}
            required
            className="input"
          />
        </Field>
        <Field label="Database name">
          <input
            value={databaseName}
            onChange={(e) => setDatabaseName(e.target.value)}
            required
            className="input"
          />
        </Field>
        <Field label="Username">
          <input value={username} onChange={(e) => setUsername(e.target.value)} required className="input" />
        </Field>
        <Field label="Password">
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="input"
          />
        </Field>
        <Field label="SSL mode">
          <select value={sslMode} onChange={(e) => setSslMode(e.target.value)} className="input">
            <option value="require">require</option>
            <option value="prefer">prefer</option>
            <option value="disable">disable</option>
          </select>
        </Field>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        type="submit"
        disabled={loading}
        className="rounded bg-black px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {loading ? "Adding..." : "Add connection"}
      </button>
    </form>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block space-y-1 text-sm">
      <span className="font-medium">{label}</span>
      {children}
    </label>
  );
}
