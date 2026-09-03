import { Alert, Button, Grid, Stack, Title } from "@mantine/core";
import { DateInput } from "@mantine/dates";
import { useForm } from "@mantine/form";
import { notifications } from "@mantine/notifications";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { JobHistoryList } from "./JobHistoryList";
import {
  cancelDailyValuesAllStationsJob,
  createDailyValuesAllStationsJob,
  deleteDailyValuesAllStationsJobs,
  listDailyValuesAllStationsJobs,
} from "./jobsApi";

const QUERY_KEY = ["jobs", "daily_values_all_stations"];

// spec/control/module/jobs.md, "Daily values (all stations)": only the
// date range, no station picker (job_type has no station_code param).
// No overlap warning and no max-range split here -- unlike the Daily
// values screen, both depend on a limit still pending empirical
// verification against the AEMET todasestaciones endpoint
// (spec/ingest/DAILY_VALUES.md), so this screen doesn't implement them
// yet and just forwards the chosen range to the service layer's own
// date_from <= date_to check.
export function DailyValuesAllStations() {
  const queryClient = useQueryClient();

  const form = useForm({
    initialValues: { date_from: null, date_to: null },
    validate: {
      date_from: (value) => (value ? null : "Obligatoria"),
      date_to: (value, values) =>
        !value ? "Obligatoria" : value < values.date_from ? "Debe ser posterior a la fecha de inicio" : null,
    },
  });

  const queueImport = useMutation({
    mutationFn: createDailyValuesAllStationsJob,
    onSuccess: () => {
      form.reset();
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
    onError: (error) => notifications.show({ color: "red", message: error.message }),
  });

  return (
    <Stack>
      <Title order={2}>Valores diarios (todas las estaciones)</Title>

      {queueImport.isError && <Alert color="red">{queueImport.error.message}</Alert>}

      <form onSubmit={form.onSubmit((values) => queueImport.mutate(values))}>
        <Grid align="flex-end">
          <Grid.Col span={{ base: 6, sm: 3 }}>
            <DateInput label="Desde" required {...form.getInputProps("date_from")} />
          </Grid.Col>
          <Grid.Col span={{ base: 6, sm: 3 }}>
            <DateInput label="Hasta" required {...form.getInputProps("date_to")} />
          </Grid.Col>
          <Grid.Col span={{ base: 12, sm: 2 }}>
            <Button type="submit" loading={queueImport.isPending} fullWidth>
              Planificar
            </Button>
          </Grid.Col>
        </Grid>
      </form>

      <JobHistoryList
        queryKey={QUERY_KEY}
        listFn={listDailyValuesAllStationsJobs}
        cancelFn={cancelDailyValuesAllStationsJob}
        deleteFn={deleteDailyValuesAllStationsJobs}
      />
    </Stack>
  );
}
