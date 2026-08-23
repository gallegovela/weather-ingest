import { Alert, Button, Center, Paper, PasswordInput, Stack, TextInput, Title } from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useLocation, useNavigate } from "react-router-dom";

import { apiClient } from "./apiClient";

// Pantalla de login (spec/control/core.md, "Estructura de la
// aplicación"): sin el layout de menú/columna, formulario centrado.
export function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();

  const form = useForm({
    initialValues: { login: "", contrasena: "" },
  });

  const mutation = useMutation({
    mutationFn: (valores) => apiClient.post("/seguridad/login", valores),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["sesion"] });
      navigate(location.state?.from?.pathname ?? "/", { replace: true });
    },
  });

  return (
    <Center h="100vh" bg="gray.0">
      <Paper withBorder shadow="md" p="xl" w={360}>
        <Title order={2} mb="lg" ta="center">
          Panel de control
        </Title>
        <form onSubmit={form.onSubmit((valores) => mutation.mutate(valores))}>
          <Stack>
            {mutation.isError && (
              // Mensaje genérico decidido en spec/control/module/seguridad.md:
              // nunca se indica cuál de los dos campos ha fallado.
              <Alert color="red">Error en los datos de entrada</Alert>
            )}
            <TextInput
              label="Usuario"
              placeholder="usuario@ejemplo.com"
              required
              {...form.getInputProps("login")}
            />
            <PasswordInput label="Contraseña" required {...form.getInputProps("contrasena")} />
            <Button type="submit" loading={mutation.isPending} fullWidth>
              Entrar
            </Button>
          </Stack>
        </form>
      </Paper>
    </Center>
  );
}
