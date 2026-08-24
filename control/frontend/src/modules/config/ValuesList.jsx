import { Alert, Button, Table, Title } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { listConfigValues } from "./configApi";
import { ValueForm } from "./ValueForm";

// Single screen (spec/control/module/config.md): no filters, no
// pagination -- the expected number of keys is small.
export function ValuesList() {
  const [editing, setEditing] = useState(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["config", "values"],
    queryFn: listConfigValues,
  });

  return (
    <>
      <Title order={2} mb="md">Config</Title>

      {isError && <Alert color="red">No se ha podido cargar la configuración.</Alert>}

      <Table striped highlightOnHover>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Clave</Table.Th>
            <Table.Th>Descripción</Table.Th>
            <Table.Th>Valor</Table.Th>
            <Table.Th>Última actualización</Table.Th>
            <Table.Th />
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {!isLoading && data?.map((configValue) => (
            <Table.Tr key={configValue.key}>
              <Table.Td>{configValue.key}</Table.Td>
              <Table.Td>{configValue.description}</Table.Td>
              <Table.Td>{configValue.value}</Table.Td>
              <Table.Td>{new Date(configValue.updated_at).toLocaleString()}</Table.Td>
              <Table.Td>
                <Button variant="subtle" size="xs" onClick={() => setEditing(configValue)}>
                  Editar
                </Button>
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>

      <ValueForm opened={editing !== null} configValue={editing} onClose={() => setEditing(null)} />
    </>
  );
}
