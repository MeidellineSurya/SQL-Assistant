"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { SQLPreview } from "@/components/query/SQLPreview";
import type { Connection, QueryHistoryItem } from "@/types";

export function QueryEditor() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [connectionId, setConnectionId] = useState("");
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<QueryHistoryItem | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.listConnections().then((conns) => {
      setConnections(conns);
      if (conns.length > 0) setConnectionId(conns[0].id);
    });
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const item = await api.generateSql(connectionId, question);
      setResult(item);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  if (connections.length === 0) {
    return (
      <p className="text-sm text-gray-600">
        Add a database connection first, then refresh its schema, before generating queries.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="space-y-3 rounded-lg border p-4">
        <label className="block space-y-1 text-sm">
          <span className="font-medium">Connection</span>
          <select
            value={connectionId}
            onChange={(e) => setConnectionId(e.target.value)}
            className="input"
          >
            {connections.map((conn) => (
              <option key={conn.id} value={conn.id}>
                {conn.name}
              </option>
            ))}
          </select>
        </label>

        <label className="block space-y-1 text-sm">
          <span className="font-medium">Ask a question about your data</span>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            required
            rows={3}
            placeholder="e.g. Which customers spent more than $100 total?"
            className="input"
          />
        </label>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="rounded bg-black px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {loading ? "Generating..." : "Generate SQL"}
        </button>
      </form>

      {result && (
        <div className="space-y-2">
          <h2 className="text-sm font-semibold">Generated SQL</h2>
          <SQLPreview sql={result.generated_sql} />
          <p className="text-xs text-gray-500">
            Saved to history. Execution arrives in a later milestone — for now this is generate-only.
          </p>
        </div>
      )}
    </div>
  );
}
