import { Alert, Button, Group, Table, TextInput, Title } from "@mantine/core";
import { DateInput } from "@mantine/dates";
import { modals } from "@mantine/modals";
import { notifications } from "@mantine/notifications";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Paginacion } from "../../app/Paginacion";
import { useSesionActual } from "../../app/SesionContext";
import { FormularioUsuario } from "./FormularioUsuario";
import { eliminarUsuario, listarUsuarios } from "./seguridadApi";

const TAMANO_PAGINA = 20;

export function ListadoUsuarios() {
  const sesion = useSesionActual();
  const queryClient = useQueryClient();

  const [pagina, setPagina] = useState(1);
  const [login, setLogin] = useState("");
  const [fechaAltaDesde, setFechaAltaDesde] = useState(null);
  const [fechaAltaHasta, setFechaAltaHasta] = useState(null);
  const [formulario, setFormulario] = useState(null); // null cerrado, {} alta, usuario edición

  const filtros = {
    pagina,
    tamano_pagina: TAMANO_PAGINA,
    login,
    fecha_alta_desde: fechaAltaDesde?.toISOString().slice(0, 10),
    fecha_alta_hasta: fechaAltaHasta?.toISOString().slice(0, 10),
  };

  const { data, isLoading, isError } = useQuery({
    queryKey: ["usuarios", filtros],
    queryFn: () => listarUsuarios(filtros),
    placeholderData: (anterior) => anterior,
  });

  const eliminar = useMutation({
    mutationFn: eliminarUsuario,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["usuarios"] });
    },
    onError: (error) => {
      notifications.show({ color: "red", message: error.message });
    },
  });

  function confirmarEliminar(usuario) {
    modals.openConfirmModal({
      title: "Eliminar usuario",
      children: `¿Seguro que quieres eliminar a "${usuario.login}"? Esta acción no se puede deshacer.`,
      labels: { confirm: "Eliminar", cancel: "Cancelar" },
      confirmProps: { color: "red" },
      onConfirm: () => eliminar.mutate(usuario.id),
    });
  }

  function actualizarFiltro(setter) {
    return (valor) => {
      setPagina(1);
      setter(valor);
    };
  }

  return (
    <>
      <Group justify="space-between" mb="md">
        <Title order={2}>Usuarios</Title>
        <Button onClick={() => setFormulario({})}>Añadir usuario</Button>
      </Group>

      <Group mb="md">
        <TextInput
          placeholder="Buscar por usuario"
          value={login}
          onChange={(e) => actualizarFiltro(setLogin)(e.currentTarget.value)}
        />
        <DateInput
          placeholder="Alta desde"
          value={fechaAltaDesde}
          onChange={actualizarFiltro(setFechaAltaDesde)}
          clearable
        />
        <DateInput
          placeholder="Alta hasta"
          value={fechaAltaHasta}
          onChange={actualizarFiltro(setFechaAltaHasta)}
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
          {data?.items.map((usuario) => (
            <Table.Tr key={usuario.id}>
              <Table.Td>{usuario.login}</Table.Td>
              <Table.Td>{new Date(usuario.fecha_alta).toLocaleString()}</Table.Td>
              <Table.Td>{new Date(usuario.fecha_actualizacion).toLocaleString()}</Table.Td>
              <Table.Td>
                <Group gap="xs" justify="flex-end">
                  <Button variant="subtle" size="xs" onClick={() => setFormulario(usuario)}>
                    Editar
                  </Button>
                  {/* Un usuario no puede eliminarse a sí mismo (spec/control/module/seguridad.md) */}
                  {usuario.id !== sesion?.id && (
                    <Button
                      variant="subtle" color="red" size="xs"
                      onClick={() => confirmarEliminar(usuario)}
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
        <Paginacion
          pagina={pagina}
          tamanoPagina={TAMANO_PAGINA}
          total={data.total}
          onCambiarPagina={setPagina}
        />
      )}

      <FormularioUsuario
        opened={formulario !== null}
        usuario={formulario?.id ? formulario : null}
        onClose={() => setFormulario(null)}
      />
    </>
  );
}
