import { Alert, Badge, Button, Checkbox, Group, Table, TextInput } from "@mantine/core";
import { DateInput } from "@mantine/dates";
import { modals } from "@mantine/modals";
import { notifications } from "@mantine/notifications";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Pagination } from "../../app/Pagination";

const PAGE_SIZE = 20;

const STATUS_COLORS = {
  pending: "gray",
  running: "blue",
  success: "green",
  error: "red",
  cancelled: "orange",
};

// Shared history list for both job-type screens (spec/control/module/jobs.md,
// "Screens"): status/date filters, per-row Cancel on `pending` jobs, and a
// selection + "Delete selected" bulk action that also covers a single row
// ("one action for one or many" -- decided in the spec, not a separate
// per-row delete button).
export function JobHistoryList({ queryKey, listFn, cancelFn, deleteFn, showStationColumn }) {
  const queryClient = useQueryClient();

  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [stationCode, setStationCode] = useState("");
  const [createdAtFrom, setCreatedAtFrom] = useState(null);
  const [createdAtTo, setCreatedAtTo] = useState(null);
  const [selected, setSelected] = useState([]);

  // Mantine's DateInput (v9) already hands back "YYYY-MM-DD" strings,
  // usable as query params as-is -- no .toISOString() conversion needed.
  const filters = {
    page,
    page_size: PAGE_SIZE,
    status,
    ...(showStationColumn ? { station_code: stationCode } : {}),
    created_at_from: createdAtFrom,
    created_at_to: createdAtTo,
  };

  const { data, isLoading, isError } = useQuery({
    queryKey: [...queryKey, filters],
    queryFn: () => listFn(filters),
    placeholderData: (previous) => previous,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey });

  const cancel = useMutation({
    mutationFn: cancelFn,
    onSuccess: invalidate,
    onError: (error) => notifications.show({ color: "red", message: error.message }),
  });

  const remove = useMutation({
    mutationFn: deleteFn,
    onSuccess: () => {
      setSelected([]);
      invalidate();
    },
    onError: (error) => notifications.show({ color: "red", message: error.message }),
  });

  function toggleSelected(id) {
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  function updateFilter(setter) {
    return (value) => {
      setPage(1);
      setter(value);
    };
  }

  function confirmDelete() {
    modals.openConfirmModal({
      title: "Eliminar jobs",
      children: `¿Seguro que quieres eliminar ${selected.length} job${selected.length === 1 ? "" : "s"}? Esta acción no se puede deshacer.`,
      labels: { confirm: "Eliminar", cancel: "Cancelar" },
      confirmProps: { color: "red" },
      onConfirm: () => remove.mutate(selected),
    });
  }

  return (
    <>
      <Group mb="md">
        <TextInput
          placeholder="Estado"
          value={status}
          onChange={(e) => updateFilter(setStatus)(e.currentTarget.value)}
        />
        {showStationColumn && (
          <TextInput
            placeholder="Estación"
            value={stationCode}
            onChange={(e) => updateFilter(setStationCode)(e.currentTarget.value)}
          />
        )}
        <DateInput placeholder="Creado desde" value={createdAtFrom} onChange={updateFilter(setCreatedAtFrom)} clearable />
        <DateInput placeholder="Creado hasta" value={createdAtTo} onChange={updateFilter(setCreatedAtTo)} clearable />
        <Button
          color="red"
          variant="light"
          disabled={selected.length === 0}
          loading={remove.isPending}
          onClick={confirmDelete}
        >
          Eliminar seleccionados
        </Button>
      </Group>

      {isError && <Alert color="red">No se ha podido cargar el histórico de jobs.</Alert>}

      <Table striped highlightOnHover>
        <Table.Thead>
          <Table.Tr>
            <Table.Th w={36} />
            <Table.Th>Id</Table.Th>
            {showStationColumn && <Table.Th>Estación</Table.Th>}
            <Table.Th>Estado</Table.Th>
            <Table.Th>Creado</Table.Th>
            <Table.Th>Insertadas</Table.Th>
            <Table.Th>Actualizadas</Table.Th>
            <Table.Th>Error</Table.Th>
            <Table.Th />
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {data?.items.map((job) => (
            <Table.Tr key={job.id}>
              <Table.Td>
                <Checkbox checked={selected.includes(job.id)} onChange={() => toggleSelected(job.id)} />
              </Table.Td>
              <Table.Td>{job.id}</Table.Td>
              {showStationColumn && <Table.Td>{job.params?.station_code}</Table.Td>}
              <Table.Td>
                <Badge color={STATUS_COLORS[job.status] ?? "gray"}>{job.status}</Badge>
              </Table.Td>
              <Table.Td>{new Date(job.created_at).toLocaleString()}</Table.Td>
              <Table.Td>{job.rows_inserted ?? "—"}</Table.Td>
              <Table.Td>{job.rows_updated ?? "—"}</Table.Td>
              <Table.Td>{job.error_message ?? ""}</Table.Td>
              <Table.Td>
                {job.status === "pending" && (
                  <Button
                    variant="subtle" size="xs" loading={cancel.isPending}
                    onClick={() => cancel.mutate(job.id)}
                  >
                    Cancelar
                  </Button>
                )}
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>

      {!isLoading && data && (
        <Pagination page={page} pageSize={PAGE_SIZE} total={data.total} onPageChange={setPage} />
      )}
    </>
  );
}
