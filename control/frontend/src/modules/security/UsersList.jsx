import { Alert, Button, Group, Table, TextInput, Title } from "@mantine/core";
import { DateInput } from "@mantine/dates";
import { modals } from "@mantine/modals";
import { notifications } from "@mantine/notifications";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Pagination } from "../../app/Pagination";
import { useCurrentSession } from "../../app/SessionContext";
import { UserForm } from "./UserForm";
import { deleteUser, listUsers } from "./securityApi";

const PAGE_SIZE = 20;

export function UsersList() {
  const session = useCurrentSession();
  const queryClient = useQueryClient();

  const [page, setPage] = useState(1);
  const [login, setLogin] = useState("");
  const [createdAtFrom, setCreatedAtFrom] = useState(null);
  const [createdAtTo, setCreatedAtTo] = useState(null);
  const [form, setForm] = useState(null); // null closed, {} create, user edit

  const filters = {
    page,
    page_size: PAGE_SIZE,
    login,
    created_at_from: createdAtFrom?.toISOString().slice(0, 10),
    created_at_to: createdAtTo?.toISOString().slice(0, 10),
  };

  const { data, isLoading, isError } = useQuery({
    queryKey: ["users", filters],
    queryFn: () => listUsers(filters),
    placeholderData: (previous) => previous,
  });

  const remove = useMutation({
    mutationFn: deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (error) => {
      notifications.show({ color: "red", message: error.message });
    },
  });

  function confirmDelete(user) {
    modals.openConfirmModal({
      title: "Eliminar usuario",
      children: `¿Seguro que quieres eliminar a "${user.login}"? Esta acción no se puede deshacer.`,
      labels: { confirm: "Eliminar", cancel: "Cancelar" },
      confirmProps: { color: "red" },
      onConfirm: () => remove.mutate(user.id),
    });
  }

  function updateFilter(setter) {
    return (value) => {
      setPage(1);
      setter(value);
    };
  }

  return (
    <>
      <Group justify="space-between" mb="md">
        <Title order={2}>Usuarios</Title>
        <Button onClick={() => setForm({})}>Añadir usuario</Button>
      </Group>

      <Group mb="md">
        <TextInput
          placeholder="Buscar por usuario"
          value={login}
          onChange={(e) => updateFilter(setLogin)(e.currentTarget.value)}
        />
        <DateInput
          placeholder="Alta desde"
          value={createdAtFrom}
          onChange={updateFilter(setCreatedAtFrom)}
          clearable
        />
        <DateInput
          placeholder="Alta hasta"
          value={createdAtTo}
          onChange={updateFilter(setCreatedAtTo)}
          clearable
        />
      </Group>

      {isError && <Alert color="red">No se ha podido cargar el listado de usuarios.</Alert>}

      <Table striped highlightOnHover>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Usuario</Table.Th>
            <Table.Th>Fecha de alta</Table.Th>
            <Table.Th>Última actualización</Table.Th>
            <Table.Th />
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {data?.items.map((user) => (
            <Table.Tr key={user.id}>
              <Table.Td>{user.login}</Table.Td>
              <Table.Td>{new Date(user.created_at).toLocaleString()}</Table.Td>
              <Table.Td>{new Date(user.updated_at).toLocaleString()}</Table.Td>
              <Table.Td>
                <Group gap="xs" justify="flex-end">
                  <Button variant="subtle" size="xs" onClick={() => setForm(user)}>
                    Editar
                  </Button>
                  {/* A user can't delete themself (spec/control/module/security.md) */}
                  {user.id !== session?.id && (
                    <Button
                      variant="subtle" color="red" size="xs"
                      onClick={() => confirmDelete(user)}
                    >
                      Eliminar
                    </Button>
                  )}
                </Group>
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>

      {!isLoading && data && (
        <Pagination
          page={page}
          pageSize={PAGE_SIZE}
          total={data.total}
          onPageChange={setPage}
        />
      )}

      <UserForm
        opened={form !== null}
        user={form?.id ? form : null}
        onClose={() => setForm(null)}
      />
    </>
  );
}
