"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { ResultsTable } from "@/components/query/ResultsTable";
import { ExplanationPanel } from "@/components/query/ExplanationPanel";
import { ChartPanel } from "@/components/charts/ChartPanel";
import type { Connection, ExecutionResult, QueryHistoryItem } from "@/types";

export function QueryEditor() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [connectionId, setConnectionId] = useState("");
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState<QueryHistoryItem | null>(null);
  const [sql, setSql] = useState("");
  const [result, setResult] = useState<ExecutionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    api.listConnections().then((conns) => {
      setConnections(conns);
      if (conns.length > 0) setConnectionId(conns[0].id);
    });
  }, []);

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setGenerating(true);
    try {
      const item = await api.generateSql(connectionId, question);
      setHistory(item);
      setSql(item.generated_sql);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setGenerating(false);
    }
  }

  async function handleRun() {
    if (!history) return;
    setError(null);
    setResult(null);
    setRunning(true);
    try {
      const { history: updated, result: execResult } = await api.executeSql(history.id, sql);
      setHistory(updated);
      if (execResult) {
        setResult(execResult);
      } else {
        setError(updated.error_message ?? "Query could not be executed");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setRunning(false);
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
      <form onSubmit={handleGenerate} className="space-y-3 rounded-lg border p-4">
        <label className="block space-y-1 text-sm">
          <span className="font-medium">Connection</span>
          <select value={connectionId} onChange={(e) => setConnectionId(e.target.value)} className="input">
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

        <button
          type="submit"
          disabled={generating}
          className="rounded bg-black px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {generating ? "Generating..." : "Generate SQL"}
        </button>
      </form>

      {history && (
        <div className="space-y-2 rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold">Generated SQL</h2>
            <span className={`text-xs ${history.is_valid ? "text-green-600" : "text-red-600"}`}>
              {history.is_valid ? "Valid" : "Invalid"}
            </span>
          </div>
          <textarea
            value={sql}
            onChange={(e) => setSql(e.target.value)}
            rows={4}
            className="input font-mono"
          />
          <p className="text-xs text-gray-500">You can edit the SQL above before running it.</p>
          <div className="flex items-center gap-4">
            <button
              onClick={handleRun}
              disabled={running}
              className="rounded bg-black px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              {running ? "Running..." : "Run query"}
            </button>
          </div>
          <ExplanationPanel key={history.id} historyId={history.id} />
        </div>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      {result && (
        <div className="space-y-2">
          <h2 className="text-sm font-semibold">Results</h2>
          <ResultsTable result={result} />
        </div>
      )}

      {result && history && <ChartPanel key={history.id} queryId={history.id} result={result} />}
    </div>
  );
}
