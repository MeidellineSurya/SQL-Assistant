"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";

export function ExplanationPanel({ historyId }: { historyId: string }) {
  const [explanation, setExplanation] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleExplain() {
    setError(null);
    setExplanation("");
    setStreaming(true);
    try {
      for await (const delta of api.streamExplanation(historyId)) {
        setExplanation((prev) => prev + delta);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setStreaming(false);
    }
  }

  return (
    <div className="space-y-2">
      <button onClick={handleExplain} disabled={streaming} className="text-sm underline disabled:opacity-50">
        {streaming ? "Explaining..." : "Explain this query"}
      </button>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {explanation && (
        <p className="rounded-lg border bg-gray-50 p-4 text-sm leading-relaxed">
          {explanation}
          {streaming && <span className="animate-pulse">▍</span>}
        </p>
      )}
    </div>
  );
}
