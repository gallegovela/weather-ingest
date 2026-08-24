import { Alert, Button, Center, Paper, PasswordInput, Stack, TextInput, Title } from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useLocation, useNavigate } from "react-router-dom";

import { apiClient } from "./apiClient";

// Login screen (spec/control/core.md, "Application structure"):
// no menu/column layout, centered form.
export function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();

  const form = useForm({
    initialValues: { login: "", password: "" },
  });

  const mutation = useMutation({
    mutationFn: (values) => apiClient.post("/security/login", values),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["session"] });
      navigate(location.state?.from?.pathname ?? "/", { replace: true });
    },
  });

  return (
    <Center h="100vh" bg="gray.0">
      <Paper withBorder shadow="md" p="xl" w={360}>
        <Title order={2} mb="lg" ta="center">
          Panel de control
        </Title>
        <form onSubmit={form.onSubmit((values) => mutation.mutate(values))}>
          <Stack>
            {mutation.isError && (
              // Generic message decided in spec/control/module/security.md:
              // never indicates which of the two fields failed.
              <Alert color="red">Error en los datos de entrada</Alert>
            )}
            <TextInput
              label="Usuario"
              placeholder="usuario@ejemplo.com"
              required
              {...form.getInputProps("login")}
            />
            <PasswordInput label="Contraseña" required {...form.getInputProps("password")} />
            <Button type="submit" loading={mutation.isPending} fullWidth>
              Entrar
            </Button>
          </Stack>
        </form>
      </Paper>
    </Center>
  );
}
