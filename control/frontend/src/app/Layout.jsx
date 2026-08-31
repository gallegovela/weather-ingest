import { AppShell, Burger, Button, Group, NavLink, Text } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { NavLink as RouterNavLink, Outlet, useNavigate } from "react-router-dom";

import { apiClient } from "./apiClient";
import { useCurrentSession } from "./SessionContext";

// Correspondence spec module -> menu entry (spec/control/core.md,
// "Application structure"): usually direct (one module = one entry
// with its `items`), but an entry can also group several modules'
// screens under `groups` of sub-headings -- decided for "Datos
// ingestados", grouping `stations` and `climatological_values` under
// an "AEMET" sub-heading (see spec/control/module/stations.md and
// spec/control/module/climatological_values.md, "Menu").
const MODULES = [
  {
    label: "Datos ingestados",
    groups: [
      {
        label: "AEMET",
        items: [
          { label: "Listado", to: "/stations/list" },
          { label: "Mapa", to: "/stations/map" },
          { label: "Valores Diarios", to: "/climatological-values/values" },
          { label: "Gráfico Valores Diarios", to: "/climatological-values/chart" },
        ],
      },
    ],
  },
  {
    label: "Seguridad",
    items: [{ label: "Usuarios", to: "/security/users" }],
  },
  {
    label: "Planificador",
    items: [
      { label: "Estaciones", to: "/jobs/stations" },
      { label: "Valores diarios", to: "/jobs/daily-values" },
    ],
  },
  {
    label: "Config",
    items: [{ label: "Valores", to: "/config/values" }],
  },
];

export function Layout() {
  const [opened, { toggle, close }] = useDisclosure();
  const session = useCurrentSession();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const logout = useMutation({
    mutationFn: () => apiClient.post("/security/logout"),
    onSuccess: () => {
      queryClient.setQueryData(["session"], undefined);
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
              {session?.login}
            </Text>
            <Button variant="subtle" size="xs" loading={logout.isPending} onClick={() => logout.mutate()}>
              Cerrar sesión
            </Button>
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        {MODULES.map((navModule) => (
          <NavLink key={navModule.label} label={navModule.label} defaultOpened childrenOffset={20}>
            {navModule.items?.map((item) => (
              <NavLink
                key={item.to}
                label={item.label}
                component={RouterNavLink}
                to={item.to}
                onClick={close}
              />
            ))}
            {navModule.groups?.map((group) => (
              <NavLink key={group.label} label={group.label} defaultOpened childrenOffset={20}>
                {group.items.map((item) => (
                  <NavLink
                    key={item.to}
                    label={item.label}
                    component={RouterNavLink}
                    to={item.to}
                    onClick={close}
                  />
                ))}
              </NavLink>
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
