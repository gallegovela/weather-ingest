// Column definitions for the `stations` table (spec/db/tables.md) and
// their filter type (spec/control/core.md, "Paginated listings with
// filters"), shared between the listing and the map's detail
// (spec/control/module/stations.md: "the same fields as in the
// listing"). `priority: 0` are the columns that never get hidden
// (station_code, name, province — decided in the spec).

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : "";
}

export const STATION_FIELDS = [
  { key: "station_code", label: "Indicativo", filterType: "text", priority: 0 },
  { key: "name", label: "Nombre", filterType: "text", priority: 0 },
  { key: "province", label: "Provincia", filterType: "text", priority: 0 },
  { key: "altitude", label: "Altitud (m)", filterType: "number_range", priority: 1 },
  { key: "synoptic_code", label: "Ind. sinóptico", filterType: "text", priority: 2 },
  {
    key: "latitude_decimal",
    label: "Latitud",
    filterType: "number_range",
    priority: 2,
  },
  {
    key: "longitude_decimal",
    label: "Longitud",
    filterType: "number_range",
    priority: 2,
  },
  { key: "latitude", label: "Latitud (GGMMSSH)", filterType: "text", priority: 3 },
  { key: "longitude", label: "Longitud (GGGMMSSH)", filterType: "text", priority: 3 },
  {
    key: "created_at",
    label: "Fecha de alta",
    filterType: "date_range",
    priority: 4,
    format: formatDate,
  },
  {
    key: "updated_at",
    label: "Última actualización",
    filterType: "date_range",
    priority: 4,
    format: formatDate,
  },
];

export const ALWAYS_VISIBLE_FIELDS = STATION_FIELDS.filter((c) => c.priority === 0);
export const OPTIONAL_FIELDS = STATION_FIELDS.filter((c) => c.priority > 0).sort(
  (a, b) => a.priority - b.priority,
);

export function formatValue(field, value) {
  if (value === null || value === undefined) return "";
  return field.format ? field.format(value) : String(value);
}
