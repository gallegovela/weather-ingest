// Column definitions for the `climatological_metrics` table
// (spec/db/tables.md), joined with `stations` for name/province, and
// their filter type (spec/control/core.md, "Paginated listings with
// filters"). `priority: 0` are the columns that never get hidden
// (station_code, name, province, date). `name`/`province` have no
// filterType -- decided in spec/control/module/metrics.md: not
// filterable here, filtering by station is `station_code` only.

function formatDate(value) {
  return value ? new Date(value).toLocaleDateString() : "";
}

function formatDateTime(value) {
  return value ? new Date(value).toLocaleString() : "";
}

export const METRIC_FIELDS = [
  { key: "station_code", label: "Indicativo", filterType: "text", priority: 0 },
  { key: "name", label: "Nombre", priority: 0 },
  { key: "province", label: "Provincia", priority: 0 },
  { key: "date", label: "Fecha", filterType: "date_range", priority: 0, format: formatDate },
  { key: "temperature_range", label: "Amplitud térmica (°C)", filterType: "number_range", priority: 1 },
  { key: "max_temperature_diff_prev_day", label: "Dif. temp. máx. día anterior (°C)", filterType: "number_range", priority: 1 },
  { key: "min_temperature_diff_prev_day", label: "Dif. temp. mín. día anterior (°C)", filterType: "number_range", priority: 1 },
  { key: "created_at", label: "Fecha de alta", filterType: "date_range", priority: 2, format: formatDateTime },
  { key: "updated_at", label: "Última actualización", filterType: "date_range", priority: 2, format: formatDateTime },
];

export const ALWAYS_VISIBLE_FIELDS = METRIC_FIELDS.filter((f) => f.priority === 0);
export const OPTIONAL_FIELDS = METRIC_FIELDS.filter((f) => f.priority > 0).sort(
  (a, b) => a.priority - b.priority,
);
export const FILTERABLE_FIELDS = METRIC_FIELDS.filter((f) => f.filterType);

export function formatValue(field, value) {
  if (value === null || value === undefined) return "";
  return field.format ? field.format(value) : String(value);
}
