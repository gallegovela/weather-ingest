import { Alert, Badge, Grid, Select, Skeleton, Stack, Title } from "@mantine/core";
import { BarChart, LineChart } from "@mantine/charts";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Rectangle } from "recharts";

import { listStations } from "../stations/stationsApi";
import {
  getClimatologicalValuesMonthlyCounts,
  getClimatologicalValuesYears,
  listClimatologicalValues,
} from "./climatologicalValuesApi";

// Reuses the stations picker endpoint unpaginated, same criterion as
// jobs' "Daily values" screen (spec/control/module/climatological_values.md,
// "Daily values chart": station filter must match that picker).
const STATIONS_PAGE_SIZE = 2000;

const MONTHS = [
  { value: "1", label: "Enero", short: "Ene" },
  { value: "2", label: "Febrero", short: "Feb" },
  { value: "3", label: "Marzo", short: "Mar" },
  { value: "4", label: "Abril", short: "Abr" },
  { value: "5", label: "Mayo", short: "May" },
  { value: "6", label: "Junio", short: "Jun" },
  { value: "7", label: "Julio", short: "Jul" },
  { value: "8", label: "Agosto", short: "Ago" },
  { value: "9", label: "Septiembre", short: "Sep" },
  { value: "10", label: "Octubre", short: "Oct" },
  { value: "11", label: "Noviembre", short: "Nov" },
  { value: "12", label: "Diciembre", short: "Dic" },
];

// A day's precipitation_raw is Ip/Acum instead of a number
// (spec/db/tables.md) -- marked with a fixed marker height (not a
// measurement, since it isn't comparable to precipitation_mm), picked
// tall enough to stay visible next to typical daily mm values.
const PRECIPITATION_SENTINEL_MARKER = 1;

const TIME_PATTERN = /^([01]\d|2[0-3]):([0-5]\d)$/;

// min/max_temperature_time, humidity_max/min_time: varchar, usually
// "HH:MM" but sometimes non-time text like "Varias" (spec/db/tables.md).
// Converted to minutes since midnight to plot as a line; anything that
// doesn't match HH:MM becomes a gap (null), same as a missing value.
function minutesSinceMidnight(value) {
  const match = typeof value === "string" ? value.match(TIME_PATTERN) : null;
  return match ? Number(match[1]) * 60 + Number(match[2]) : null;
}

function formatMinutesAsTime(value) {
  if (value === null || value === undefined) return "";
  const hours = Math.floor(value / 60);
  const minutes = value % 60;
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

// Decimal columns arrive as strings over JSON (pydantic's default
// Decimal serialization) -- same conversion already used by
// stations/Map.jsx for latitude_decimal/longitude_decimal.
function toNumber(value) {
  return value === null || value === undefined ? null : Number(value);
}

function daysInMonth(year, month) {
  return new Date(year, month, 0).getDate();
}

export function DailyValuesChart() {
  const [stationCode, setStationCode] = useState(null);
  // null = no explicit choice, fall back to the most recent year with
  // data once `years` loads (derived below, not an effect: `years`
  // arrives descending, see
  // spec/control/module/climatological_values.md).
  const [selectedYear, setSelectedYear] = useState(null);
  const [month, setMonth] = useState(null);

  const { data: stationsPage } = useQuery({
    queryKey: ["stations", "picker"],
    queryFn: () => listStations({ page_size: STATIONS_PAGE_SIZE }),
  });
  const stationOptions = (stationsPage?.items ?? []).map((station) => ({
    value: station.station_code,
    label: `${station.station_code} — ${station.name}`,
  }));

  const {
    data: years,
    isError: isYearsError,
  } = useQuery({
    queryKey: ["climatological-values", "years", stationCode],
    queryFn: () => getClimatologicalValuesYears({ station_code: stationCode }),
    enabled: !!stationCode,
  });

  const year = selectedYear ?? (years && years.length > 0 ? String(years[0]) : null);

  const {
    data: monthlyCounts,
    isError: isMonthlyCountsError,
  } = useQuery({
    queryKey: ["climatological-values", "monthly-counts", stationCode, year],
    queryFn: () => getClimatologicalValuesMonthlyCounts({ station_code: stationCode, year }),
    enabled: !!stationCode && !!year,
  });

  const monthlyData = MONTHS.map((m, index) => ({
    month: m.value,
    label: m.short,
    count: monthlyCounts?.[index] ?? 0,
  }));

  function selectMonthFromChart(state) {
    if (typeof state?.activeIndex === "number") {
      setMonth(monthlyData[state.activeIndex]?.month ?? null);
    }
  }

  const dateFrom = stationCode && year && month ? `${year}-${month.padStart(2, "0")}-01` : null;
  const dateTo =
    stationCode && year && month
      ? `${year}-${month.padStart(2, "0")}-${String(daysInMonth(Number(year), Number(month))).padStart(2, "0")}`
      : null;

  const {
    data: monthValues,
    isLoading: isMonthValuesLoading,
    isError: isMonthValuesError,
  } = useQuery({
    queryKey: ["climatological-values", "month-values", stationCode, dateFrom, dateTo],
    queryFn: () =>
      listClimatologicalValues({
        station_code: stationCode, date_from: dateFrom, date_to: dateTo, page_size: 31,
      }),
    enabled: !!dateFrom && !!dateTo,
  });

  const chartData = useMemo(() => {
    const items = monthValues?.items ?? [];
    return items
      .slice()
      .sort((a, b) => a.date.localeCompare(b.date))
      .map((v) => ({
        day: v.date.slice(-2),
        mean_temperature: toNumber(v.mean_temperature),
        max_temperature: toNumber(v.max_temperature),
        min_temperature: toNumber(v.min_temperature),
        min_temperature_time: minutesSinceMidnight(v.min_temperature_time),
        max_temperature_time: minutesSinceMidnight(v.max_temperature_time),
        sunshine_hours: toNumber(v.sunshine_hours),
        precipitation_mm: toNumber(v.precipitation_mm),
        precipitation_sentinel:
          v.precipitation_raw === "Ip" || v.precipitation_raw === "Acum"
            ? PRECIPITATION_SENTINEL_MARKER
            : null,
        humidity_max: toNumber(v.humidity_max),
        humidity_min: toNumber(v.humidity_min),
        humidity_max_time: minutesSinceMidnight(v.humidity_max_time),
        humidity_min_time: minutesSinceMidnight(v.humidity_min_time),
        wind_mean_speed: toNumber(v.wind_mean_speed),
      }));
  }, [monthValues]);

  const hasPrecipitationSentinel = chartData.some((d) => d.precipitation_sentinel !== null);

  return (
    <Stack>
      <Title order={2}>Gráfico Valores Diarios</Title>

      <Grid align="flex-end">
        <Grid.Col span={{ base: 12, sm: 4 }}>
          <Select
            label="Estación"
            placeholder="Buscar por código o nombre"
            data={stationOptions}
            searchable
            clearable
            value={stationCode}
            onChange={(value) => {
              setStationCode(value);
              setSelectedYear(null);
              setMonth(null);
            }}
          />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 3 }}>
          <Select
            label="Año"
            placeholder={stationCode ? "Elige un año" : "Elige antes una estación"}
            data={(years ?? []).map((y) => String(y))}
            value={year}
            onChange={(value) => {
              setSelectedYear(value);
              setMonth(null);
            }}
            disabled={!stationCode}
          />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 3 }}>
          <Select
            label="Mes"
            placeholder={year ? "Elige un mes" : "Elige antes un año"}
            data={MONTHS}
            value={month}
            onChange={setMonth}
            disabled={!year}
          />
        </Grid.Col>
      </Grid>

      {isYearsError && <Alert color="red">No se han podido cargar los años disponibles.</Alert>}

      {stationCode && year && (
        <Stack gap="xs">
          <Title order={4}>Valores importados por mes</Title>
          {isMonthlyCountsError && (
            <Alert color="red">No se ha podido cargar el resumen mensual.</Alert>
          )}
          <BarChart
            h={220}
            data={monthlyData}
            dataKey="label"
            series={[{ name: "count", label: "Valores importados", color: "blue.4" }]}
            barChartProps={{ onClick: selectMonthFromChart }}
            barProps={{
              cursor: "pointer",
              shape: (props) => (
                <Rectangle
                  {...props}
                  fill={props.payload?.month === month ? "var(--mantine-color-blue-7)" : props.fill}
                />
              ),
            }}
          />
        </Stack>
      )}

      {month && (
        <Stack gap="xl">
          {isMonthValuesLoading && <Skeleton height={220} />}
          {isMonthValuesError && (
            <Alert color="red">No se han podido cargar los valores diarios del mes.</Alert>
          )}

          {!isMonthValuesLoading && !isMonthValuesError && (
            <>
              <Stack gap="xs">
                <Title order={4}>Temperaturas</Title>
                <LineChart
                  h={220}
                  data={chartData}
                  dataKey="day"
                  connectNulls={false}
                  withLegend
                  series={[
                    { name: "mean_temperature", label: "Media (°C)", color: "yellow.6" },
                    { name: "max_temperature", label: "Máxima (°C)", color: "red.6" },
                    { name: "min_temperature", label: "Mínima (°C)", color: "blue.6" },
                  ]}
                />
              </Stack>

              <Stack gap="xs">
                <Title order={4}>Hora temperaturas extremas</Title>
                <LineChart
                  h={220}
                  data={chartData}
                  dataKey="day"
                  connectNulls={false}
                  withLegend
                  valueFormatter={formatMinutesAsTime}
                  series={[
                    { name: "max_temperature_time", label: "Hora temp. máxima", color: "red.6" },
                    { name: "min_temperature_time", label: "Hora temp. mínima", color: "blue.6" },
                  ]}
                />
              </Stack>

              <Stack gap="xs">
                <Title order={4}>Insolación</Title>
                <LineChart
                  h={220}
                  data={chartData}
                  dataKey="day"
                  connectNulls={false}
                  series={[{ name: "sunshine_hours", label: "Insolación (h)", color: "orange.6" }]}
                />
              </Stack>

              <Stack gap="xs">
                <Title order={4}>Precipitación</Title>
                {hasPrecipitationSentinel && (
                  <Alert color="yellow" variant="light" title="Leyenda">
                    <Badge color="yellow" variant="filled" mr="xs">Ip / Acum</Badge>
                    Los días marcados tienen un valor de precipitación no numérico:{" "}
                    <b>Ip</b> (lluvia inapreciable, menos de 0,1 mm) o <b>Acum</b> (valor
                    acumulado en un día posterior).
                  </Alert>
                )}
                <BarChart
                  h={220}
                  data={chartData}
                  dataKey="day"
                  series={[
                    { name: "precipitation_mm", label: "Precipitación (mm)", color: "blue.6" },
                    { name: "precipitation_sentinel", label: "Ip / Acum", color: "yellow.6" },
                  ]}
                />
              </Stack>

              <Stack gap="xs">
                <Title order={4}>Humedad</Title>
                <LineChart
                  h={220}
                  data={chartData}
                  dataKey="day"
                  connectNulls={false}
                  withLegend
                  series={[
                    { name: "humidity_max", label: "Máxima (%)", color: "teal.6" },
                    { name: "humidity_min", label: "Mínima (%)", color: "cyan.6" },
                  ]}
                />
              </Stack>

              <Stack gap="xs">
                <Title order={4}>Hora humedad extremas</Title>
                <LineChart
                  h={220}
                  data={chartData}
                  dataKey="day"
                  connectNulls={false}
                  withLegend
                  valueFormatter={formatMinutesAsTime}
                  series={[
                    { name: "humidity_max_time", label: "Hora humedad máxima", color: "teal.6" },
                    { name: "humidity_min_time", label: "Hora humedad mínima", color: "cyan.6" },
                  ]}
                />
              </Stack>

              <Stack gap="xs">
                <Title order={4}>Viento</Title>
                <LineChart
                  h={220}
                  data={chartData}
                  dataKey="day"
                  connectNulls={false}
                  series={[{ name: "wind_mean_speed", label: "Vel. media (m/s)", color: "grape.6" }]}
                />
              </Stack>
            </>
          )}
        </Stack>
      )}
    </Stack>
  );
}
