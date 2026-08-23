import { AppShell, Burger, Button, Group, NavLink, Text } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { NavLink as RouterNavLink, Outlet, useNavigate } from "react-router-dom";

import { apiClient } from "./apiClient";
import { useSesionActual } from "./SesionContext";

// Correspondencia directa módulo de la spec -> entrada de menú con sus
// subitems (spec/control/core.md, "Estructura de la aplicación").
const MODULOS = [
  {
    etiqueta: "Estaciones",
    items: [
      { etiqueta: "Listado", to: "/estaciones/listado" },
      { etiqueta: "Mapa", to: "/estaciones/mapa" },
    ],
  },
  {
    etiqueta: "Seguridad",
    items: [{ etiqueta: "Usuarios", to: "/seguridad/usuarios" }],
  },
];

export function Layout() {
  const [opened, { toggle }] = useDisclosure();
  const sesion = useSesionActual();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const logout = useMutation({
    mutationFn: () => apiClient.post("/seguridad/logout"),
    onSuccess: () => {
      queryClient.setQueryData(["sesion"], undefined);
      navigate("/login", { replace: true });
    },
  });

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{ width: 260, breakpoint: "sm", collapsed: { mobile: !opened } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            <Text fw={700}>Panel de control</Text>
          </Group>
          <Group>
            <Text size="sm" c="dimmed">
              {sesion?.login}
            </Text>
            <Button variant="subtle" size="xs" loading={logout.isPending} onClick={() => logout.mutate()}>
              Cerrar sesión
            </Button>
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        {MODULOS.map((modulo) => (
          <NavLink key={modulo.etiqueta} label={modulo.etiqueta} defaultOpened childrenOffset={20}>
            {modulo.items.map((item) => (
              <NavLink key={item.to} label={item.etiqueta} component={RouterNavLink} to={item.to} />
            ))}
          </NavLink>
        ))}
      </AppShell.Navbar>

      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
}
