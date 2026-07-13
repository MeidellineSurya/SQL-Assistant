"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import { DynamicChart } from "@/components/charts/DynamicChart";
import type { Chart, ChartType, ExecutionResult } from "@/types";

const CHART_TYPES: ChartType[] = ["bar", "line", "pie", "scatter"];

export function ChartPanel({ queryId, result }: { queryId: string; result: ExecutionResult }) {
  const [reasoning, setReasoning] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<ChartType>("bar");
  const [chart, setChart] = useState<Chart | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [suggesting, setSuggesting] = useState(false);
  const [generating, setGenerating] = useState(false);

  async function handleSuggest() {
    setError(null);
    setChart(null);
    setSuggesting(true);
    try {
      const suggestion = await api.suggestChart(queryId, result.columns, result.rows.slice(0, 5));
      setReasoning(suggestion.reasoning);
      if (suggestion.chart_type !== "table") {
        setSelectedType(suggestion.chart_type);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setSuggesting(false);
    }
  }

  async function handleGenerate() {
    setError(null);
    setGenerating(true);
    try {
      const generated = await api.generateChart(queryId, selectedType, result.columns);
      setChart(generated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="space-y-3 rounded-lg border p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold">Visualize</h2>
        <button onClick={handleSuggest} disabled={suggesting} className="text-sm underline disabled:opacity-50">
          {suggesting ? "Asking AI..." : "Suggest chart type"}
        </button>
      </div>

      {reasoning && <p className="text-xs text-gray-500">AI suggests: {reasoning}</p>}

      <div className="flex items-center gap-2">
        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value as ChartType)}
          className="input w-auto"
        >
          {CHART_TYPES.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="rounded bg-black px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {generating ? "Generating..." : "Generate chart"}
        </button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {chart && <DynamicChart chartType={chart.chart_type} config={chart.config_json} result={result} />}
    </div>
  );
}
