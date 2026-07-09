"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { ConnectionForm } from "@/components/connections/ConnectionForm";
import type { Connection, SchemaTable } from "@/types";

export default function ConnectionsPage() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [loading, setLoading] = useState(true);
  const [testResults, setTestResults] = useState<Record<string, string>>({});
  const [schemas, setSchemas] = useState<Record<string, SchemaTable[]>>({});

  useEffect(() => {
    api
      .listConnections()
      .then(setConnections)
      .finally(() => setLoading(false));
  }, []);

  function handleCreated(conn: Connection) {
    setConnections((prev) => [...prev, conn]);
  }

  async function handleDelete(id: string) {
    await api.deleteConnection(id);
    setConnections((prev) => prev.filter((c) => c.id !== id));
  }

  async function handleTest(id: string) {
    setTestResults((prev) => ({ ...prev, [id]: "Testing..." }));
    try {
      const result = await api.testConnection(id);
      setTestResults((prev) => ({
        ...prev,
        [id]: result.success ? `Connected (${result.latency_ms}ms)` : `Failed: ${result.error}`,
      }));
    } catch (err) {
      setTestResults((prev) => ({ ...prev, [id]: err instanceof ApiError ? err.message : "Failed" }));
    }
  }

  async function handleRefreshSchema(id: string) {
    const result = await api.refreshConnectionSchema(id);
    setSchemas((prev) => ({ ...prev, [id]: result.schema_cache?.tables ?? [] }));
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold">Database Connections</h1>
        <p className="mt-1 text-sm text-gray-600">
          Add a connection to your own PostgreSQL database. Credentials are encrypted at rest and only decrypted
          server-side, per-request, to run a query on your behalf.
        </p>
      </div>

      <ConnectionForm onCreated={handleCreated} />

      <div className="space-y-3">
        <h2 className="text-sm font-semibold">Your connections</h2>
        {loading && <p className="text-sm text-gray-600">Loading...</p>}
        {!loading && connections.length === 0 && (
          <p className="text-sm text-gray-600">No connections yet.</p>
        )}
        {connections.map((conn) => (
          <div key={conn.id} className="rounded-lg border p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">{conn.name}</p>
                <p className="text-sm text-gray-600">
                  {conn.username}@{conn.host}:{conn.port}/{conn.database_name}
                </p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => handleTest(conn.id)} className="rounded border px-3 py-1 text-sm">
                  Test
                </button>
                <button
                  onClick={() => handleRefreshSchema(conn.id)}
                  className="rounded border px-3 py-1 text-sm"
                >
                  Refresh schema
                </button>
                <button
                  onClick={() => handleDelete(conn.id)}
                  className="rounded border border-red-300 px-3 py-1 text-sm text-red-600"
                >
                  Delete
                </button>
              </div>
            </div>

            {testResults[conn.id] && <p className="mt-2 text-sm">{testResults[conn.id]}</p>}

            {schemas[conn.id] && (
              <ul className="mt-2 space-y-1 text-sm text-gray-700">
                {schemas[conn.id].map((table) => (
                  <li key={table.name}>
                    <span className="font-mono">{table.name}</span>{" "}
                    <span className="text-gray-500">({table.columns.length} columns)</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
