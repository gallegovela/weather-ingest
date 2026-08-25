import { Alert, Button, Grid, Select, Stack, Title } from "@mantine/core";
import { DateInput } from "@mantine/dates";
import { useForm } from "@mantine/form";
import { modals } from "@mantine/modals";
import { notifications } from "@mantine/notifications";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { listConfigValues } from "../config/configApi";
import { listStations } from "../stations/stationsApi";
import { JobHistoryList } from "./JobHistoryList";
import { cancelDailyValuesJob, createDailyValuesJob, deleteDailyValuesJobs, listDailyValuesJobs } from "./jobsApi";

const QUERY_KEY = ["jobs", "daily_values"];
// Reuses the existing stations endpoint for the picker, unpaginated --
// same criterion as the stations map (spec/control/module/stations.md):
// ~921 rows isn't a volume that justifies paginating a picker.
const STATIONS_PAGE_SIZE = 2000;

// Mantine's DateInput (v9) hands back a "YYYY-MM-DD" string, not a
// Date -- form.values.date_from/date_to are already strings, usable
// as-is for the API and for string comparison (date_to's validator
// below), but need parsing to Date for arithmetic (day counts,
// splitRange).
function formatISODate(date) {
  return date.toISOString().slice(0, 10);
}

// Splits [dateFrom, dateTo] (ISO date strings) into consecutive
// windows of at most maxDays each (spec/control/module/jobs.md,
// "Splitting a too-large range"), as Date objects.
function splitRange(dateFrom, dateTo, maxDays) {
  const windows = [];
  let start = new Date(dateFrom);
  const end = new Date(dateTo);

  while (start <= end) {
    const windowEnd = new Date(start);
    windowEnd.setDate(windowEnd.getDate() + maxDays - 1);
    if (windowEnd > end) windowEnd.setTime(end.getTime());
    windows.push([new Date(start), new Date(windowEnd)]);
    start = new Date(windowEnd);
    start.setDate(start.getDate() + 1);
  }

  return windows;
}

export function DailyValues() {
  const queryClient = useQueryClient();

  const form = useForm({
    initialValues: { station_code: null, date_from: null, date_to: null },
    validate: {
      station_code: (value) => (value ? null : "Elige una estación"),
      date_from: (value) => (value ? null : "Obligatoria"),
      date_to: (value, values) =>
        !value ? "Obligatoria" : value < values.date_from ? "Debe ser posterior a la fecha de inicio" : null,
    },
  });

  const { data: stationsPage } = useQuery({
    queryKey: ["stations", "picker"],
    queryFn: () => listStations({ page_size: STATIONS_PAGE_SIZE }),
  });
  const stationOptions = (stationsPage?.items ?? []).map((station) => ({
    value: station.station_code,
    label: `${station.station_code} — ${station.name}`,
  }));

  const { data: configValues } = useQuery({ queryKey: ["config", "values"], queryFn: listConfigValues });
  const maxDateRange = Number(
    configValues?.find((v) => v.key === "SCHEDULER_MAX_DATE_RANGE")?.value ?? Infinity
  );

  const invalidate = () => queryClient.invalidateQueries({ queryKey: QUERY_KEY });

  const queueOne = useMutation({
    mutationFn: createDailyValuesJob,
    onSuccess: invalidate,
    onError: (error) => notifications.show({ color: "red", message: error.message }),
  });

  const queueSplit = useMutation({
    mutationFn: (windows) =>
      Promise.all(
        windows.map(([from, to]) =>
          createDailyValuesJob({
            station_code: form.values.station_code,
            date_from: formatISODate(from),
            date_to: formatISODate(to),
          })
        )
      ),
    onSuccess: invalidate,
    onError: (error) => notifications.show({ color: "red", message: error.message }),
  });

  function submit(values) {
    const days =
      Math.floor((new Date(values.date_to) - new Date(values.date_from)) / (1000 * 60 * 60 * 24)) + 1;

    if (days <= maxDateRange) {
      queueOne.mutate({
        station_code: values.station_code,
        date_from: values.date_from,
        date_to: values.date_to,
      });
      return;
    }

    const windows = splitRange(values.date_from, values.date_to, maxDateRange);
    modals.openConfirmModal({
      title: "El rango supera el máximo permitido",
      children: `El rango elegido son ${days} días; el máximo por importación es de ${maxDateRange}. `
        + `¿Quieres partirlo en ${windows.length} planificaciones, o prefieres redefinir el rango?`,
      labels: { confirm: `Partir en ${windows.length} planificaciones`, cancel: "Redefinir rango" },
      onConfirm: () => queueSplit.mutate(windows),
    });
  }

  return (
    <Stack>
      <Title order={2}>Valores diarios</Title>

      {(queueOne.isError || queueSplit.isError) && (
        <Alert color="red">{(queueOne.error ?? queueSplit.error)?.message}</Alert>
      )}

      <form onSubmit={form.onSubmit(submit)}>
        <Grid align="flex-end">
          <Grid.Col span={{ base: 12, sm: 4 }}>
            <Select
              label="Estación"
              placeholder="Buscar por código o nombre"
              data={stationOptions}
              searchable
              required
              {...form.getInputProps("station_code")}
            />
          </Grid.Col>
          <Grid.Col span={{ base: 6, sm: 3 }}>
            <DateInput label="Desde" required {...form.getInputProps("date_from")} />
          </Grid.Col>
          <Grid.Col span={{ base: 6, sm: 3 }}>
            <DateInput label="Hasta" required {...form.getInputProps("date_to")} />
          </Grid.Col>
          <Grid.Col span={{ base: 12, sm: 2 }}>
            <Button type="submit" loading={queueOne.isPending || queueSplit.isPending} fullWidth>
              Planificar
            </Button>
          </Grid.Col>
        </Grid>
      </form>

      <JobHistoryList
        queryKey={QUERY_KEY}
        listFn={listDailyValuesJobs}
        cancelFn={cancelDailyValuesJob}
        deleteFn={deleteDailyValuesJobs}
        showStationColumn
      />
    </Stack>
  );
}
