import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChartConfig, ChartType, ExecutionResult } from "@/types";

const COLORS = ["#2563eb", "#16a34a", "#d97706", "#dc2626", "#7c3aed", "#0891b2"];

function toChartData(result: ExecutionResult, config: ChartConfig): Record<string, string | number>[] {
  return result.rows.map((row) => {
    const record: Record<string, string | number> = {};
    result.columns.forEach((col, i) => {
      record[col] = row[i] as string | number;
    });
    config.y_keys.forEach((key) => {
      const value = record[key];
      if (typeof value === "string") record[key] = Number(value);
    });
    // Recharts' categorical axis needs a stable string/number tick identity.
    // A raw boolean (e.g. from `GROUP BY is_valid`) or null breaks its
    // internal band-scale domain and silently renders no ticks or bars at
    // all, rather than an obvious error.
    record[config.x_key] = String(record[config.x_key]);
    return record;
  });
}

export function DynamicChart({
  chartType,
  config,
  result,
}: {
  chartType: ChartType;
  config: ChartConfig;
  result: ExecutionResult;
}) {
  const data = toChartData(result, config);

  if (chartType === "bar") {
    return (
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={config.x_key} />
          <YAxis />
          <Tooltip />
          <Legend />
          {config.y_keys.map((key, i) => (
            <Bar key={key} dataKey={key} fill={COLORS[i % COLORS.length]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    );
  }

  if (chartType === "line") {
    return (
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={config.x_key} />
          <YAxis />
          <Tooltip />
          <Legend />
          {config.y_keys.map((key, i) => (
            <Line key={key} type="monotone" dataKey={key} stroke={COLORS[i % COLORS.length]} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    );
  }

  if (chartType === "pie") {
    const valueKey = config.y_keys[0];
    return (
      <ResponsiveContainer width="100%" height={320}>
        <PieChart>
          <Tooltip />
          <Legend />
          <Pie data={data} dataKey={valueKey} nameKey={config.x_key} outerRadius={110} label>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
    );
  }

  if (chartType === "scatter") {
    const valueKey = config.y_keys[0];
    return (
      <ResponsiveContainer width="100%" height={320}>
        <ScatterChart>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={config.x_key} name={config.x_key} />
          <YAxis dataKey={valueKey} name={valueKey} />
          <Tooltip cursor={{ strokeDasharray: "3 3" }} />
          <Scatter data={data} fill={COLORS[0]} />
        </ScatterChart>
      </ResponsiveContainer>
    );
  }

  return <p className="text-sm text-gray-600">No chart available for this data — try the results table instead.</p>;
}
