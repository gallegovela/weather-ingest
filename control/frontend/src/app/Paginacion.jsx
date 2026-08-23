import { Group, Pagination, Text } from "@mantine/core";

// Control de paginación reutilizado por cualquier listado del panel
// (convención transversal "Listados paginados con filtros",
// spec/control/core.md).
export function Paginacion({ pagina, tamanoPagina, total, onCambiarPagina }) {
  const totalPaginas = Math.max(1, Math.ceil(total / tamanoPagina));

  return (
    <Group justify="space-between" mt="md">
      <Text size="sm" c="dimmed">
        {total} resultado{total === 1 ? "" : "s"}
      </Text>
      <Pagination value={pagina} onChange={onCambiarPagina} total={totalPaginas} />
    </Group>
  );
}
