// Column definitions for the `climatological_values` table
// (spec/db/tables.md), joined with `stations` for name/province, and
// their filter type (spec/control/core.md, "Paginated listings with
// filters"). `priority: 0` are the columns that never get hidden
// (station_code, name, province, date). `name`/`province` have no
// filterType -- decided in spec/control/module/climatological_values.md:
// not filterable here, filtering by station is `station_code` only.

function formatDate(value) {
  return value ? new Date(value).toLocaleDateString() : "";
}

function formatDateTime(value) {
  return value ? new Date(value).toLocaleString() : "";
}

export const VALUE_FIELDS = [
  { key: "station_code", label: "Indicativo", filterType: "text", priority: 0 },
  { key: "name", label: "Nombre", priority: 0 },
  { key: "province", label: "Provincia", priority: 0 },
  { key: "date", label: "Fecha", filterType: "date_range", priority: 0, format: formatDate },
  { key: "mean_temperature", label: "Temp. media (°C)", filterType: "number_range", priority: 1 },
  { key: "min_temperature", label: "Temp. mínima (°C)", filterType: "number_range", priority: 1 },
  { key: "max_temperature", label: "Temp. máxima (°C)", filterType: "number_range", priority: 1 },
  { key: "precipitation_mm", label: "Precipitación (mm)", filterType: "number_range", priority: 1 },
  { key: "precipitation_raw", label: "Precipitación (original)", filterType: "text", priority: 2 },
  { key: "wind_mean_speed", label: "Vel. media viento (m/s)", filterType: "number_range", priority: 2 },
  { key: "wind_gust_speed", label: "Racha máxima (m/s)", filterType: "number_range", priority: 2 },
  { key: "wind_gust_direction", label: "Dirección racha (decenas de grado)", filterType: "number_range", priority: 3 },
  { key: "sunshine_hours", label: "Insolación (h)", filterType: "number_range", priority: 2 },
  { key: "pressure_max", label: "Presión máxima (hPa)", filterType: "number_range", priority: 3 },
  { key: "pressure_min", label: "Presión mínima (hPa)", filterType: "number_range", priority: 3 },
  { key: "humidity_mean", label: "Humedad media (%)", filterType: "number_range", priority: 2 },
  { key: "humidity_max", label: "Humedad máxima (%)", filterType: "number_range", priority: 3 },
  { key: "humidity_min", label: "Humedad mínima (%)", filterType: "number_range", priority: 3 },
  { key: "precipitation_intensity_max", label: "Intensidad máx. precipitación (mm/h)", filterType: "number_range", priority: 3 },
  { key: "min_temperature_time", label: "Hora temp. mínima", filterType: "text", priority: 4 },
  { key: "max_temperature_time", label: "Hora temp. máxima", filterType: "text", priority: 4 },
  { key: "wind_gust_time", label: "Hora racha máxima", filterType: "text", priority: 4 },
  { key: "pressure_max_time", label: "Hora presión máxima", filterType: "text", priority: 4 },
  { key: "pressure_min_time", label: "Hora presión mínima", filterType: "text", priority: 4 },
  { key: "humidity_max_time", label: "Hora humedad máxima", filterType: "text", priority: 4 },
  { key: "humidity_min_time", label: "Hora humedad mínima", filterType: "text", priority: 4 },
  { key: "precipitation_intensity_max_time", label: "Hora intensidad máx.", filterType: "text", priority: 4 },
  { key: "created_at", label: "Fecha de alta", filterType: "date_range", priority: 5, format: formatDateTime },
  { key: "updated_at", label: "Última actualización", filterType: "date_range", priority: 5, format: formatDateTime },
];

export const ALWAYS_VISIBLE_FIELDS = VALUE_FIELDS.filter((f) => f.priority === 0);
export const OPTIONAL_FIELDS = VALUE_FIELDS.filter((f) => f.priority > 0).sort(
  (a, b) => a.priority - b.priority,
);
export const FILTERABLE_FIELDS = VALUE_FIELDS.filter((f) => f.filterType);

export function formatValue(field, value) {
  if (value === null || value === undefined) return "";
  return field.format ? field.format(value) : String(value);
}
