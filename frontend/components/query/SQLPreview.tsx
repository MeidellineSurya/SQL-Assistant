export function SQLPreview({ sql }: { sql: string }) {
  return (
    <pre className="overflow-x-auto rounded-lg border bg-gray-50 p-4 font-mono text-sm">
      <code>{sql}</code>
    </pre>
  );
}
