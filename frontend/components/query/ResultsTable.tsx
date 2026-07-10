import type { ExecutionResult } from "@/types";

export function ResultsTable({ result }: { result: ExecutionResult }) {
  if (result.rows.length === 0) {
    return <p className="text-sm text-gray-600">Query ran successfully, no rows returned.</p>;
  }

  return (
    <div className="space-y-2">
      <div className="overflow-x-auto rounded-lg border">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              {result.columns.map((col) => (
                <th key={col} className="px-3 py-2 text-left font-medium">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {result.rows.map((row, i) => (
              <tr key={i} className="border-t">
                {row.map((cell, j) => (
                  <td key={j} className="px-3 py-2 font-mono">
                    {cell === null ? <span className="text-gray-400">NULL</span> : String(cell)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-gray-500">
        {result.row_count} row{result.row_count === 1 ? "" : "s"}
        {result.truncated && " (truncated — more rows available)"}
      </p>
    </div>
  );
}
