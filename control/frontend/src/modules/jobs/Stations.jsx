import { Alert, Button, Stack, Title } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { JobHistoryList } from "./JobHistoryList";
import { cancelStationsJob, createStationsJob, deleteStationsJobs, listStationsJobs } from "./jobsApi";

const QUERY_KEY = ["jobs", "stations"];

// spec/control/module/jobs.md, "Stations": no parameters, just queue +
// history.
export function Stations() {
  const queryClient = useQueryClient();

  const queueImport = useMutation({
    mutationFn: createStationsJob,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: QUERY_KEY }),
    onError: (error) => notifications.show({ color: "red", message: error.message }),
  });

  return (
    <Stack>
      <Title order={2}>Estaciones</Title>

      {queueImport.isError && <Alert color="red">{queueImport.error.message}</Alert>}

      <Button w="fit-content" loading={queueImport.isPending} onClick={() => queueImport.mutate()}>
        Planificar importación
      </Button>

      <JobHistoryList
        queryKey={QUERY_KEY}
        listFn={listStationsJobs}
        cancelFn={cancelStationsJob}
        deleteFn={deleteStationsJobs}
      />
    </Stack>
  );
}
