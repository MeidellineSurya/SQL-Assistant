"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { SQLPreview } from "@/components/query/SQLPreview";
import type { QueryHistoryItem } from "@/types";

export default function HistoryPage() {
  const [items, setItems] = useState<QueryHistoryItem[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listHistory().then((page) => {
      setItems(page.items);
      setCursor(page.next_cursor);
      setLoading(false);
    });
  }, []);

  async function loadMore() {
    if (!cursor) return;
    setLoading(true);
    const page = await api.listHistory(cursor);
    setItems((prev) => [...prev, ...page.items]);
    setCursor(page.next_cursor);
    setLoading(false);
  }

  async function handleDelete(id: string) {
    await api.deleteHistoryItem(id);
    setItems((prev) => prev.filter((item) => item.id !== id));
  }

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-semibold">Query History</h1>

      {loading && items.length === 0 && <p className="text-sm text-gray-600">Loading...</p>}
      {!loading && items.length === 0 && <p className="text-sm text-gray-600">No queries yet.</p>}

      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.id} className="rounded-lg border p-4">
            <div className="flex items-start justify-between gap-4">
              <p className="text-sm font-medium">{item.natural_language}</p>
              <button
                onClick={() => handleDelete(item.id)}
                className="shrink-0 rounded border border-red-300 px-2 py-1 text-xs text-red-600"
              >
                Delete
              </button>
            </div>
            <div className="mt-2">
              <SQLPreview sql={item.generated_sql} />
            </div>
            <p className="mt-1 text-xs text-gray-500">{new Date(item.created_at).toLocaleString()}</p>
          </div>
        ))}
      </div>

      {cursor && (
        <button onClick={loadMore} disabled={loading} className="text-sm underline">
          {loading ? "Loading..." : "Load more"}
        </button>
      )}
    </div>
  );
}
