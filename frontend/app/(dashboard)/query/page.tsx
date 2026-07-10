import { QueryEditor } from "@/components/query/QueryEditor";

export default function QueryPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold">Query</h1>
        <p className="mt-1 text-sm text-gray-600">Ask a question in plain English, get back SQL.</p>
      </div>
      <QueryEditor />
    </div>
  );
}
