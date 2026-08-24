import { Alert, Button, Group, Modal, PasswordInput, Stack, TextInput } from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { createUser, updateUser } from "./securityApi";

// Add/edit user form (spec/control/module/security.md, screens 3 and
// 4): a single component reused for both, following the organization
// set in spec/control/core.md.
export function UserForm({ opened, user, onClose }) {
  const editing = Boolean(user);
  const queryClient = useQueryClient();

  const form = useForm({
    initialValues: { login: "", password: "" },
    validate: {
      login: (value) => (/^\S+@\S+\.\S+$/.test(value) ? null : "Formato de email no válido"),
      password: (value) => (!editing && !value ? "La contraseña es obligatoria" : null),
    },
  });

  useEffect(() => {
    if (opened) {
      form.setValues({ login: user?.login ?? "", password: "" });
      form.clearErrors();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, user]);

  const mutation = useMutation({
    mutationFn: (values) => {
      const data = { login: values.login };
      if (values.password) data.password = values.password;
      return editing ? updateUser(user.id, data) : createUser({ ...data, password: values.password });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      onClose();
    },
  });

  return (
    <Modal opened={opened} onClose={onClose} title={editing ? "Editar usuario" : "Añadir usuario"}>
      <form onSubmit={form.onSubmit((values) => mutation.mutate(values))}>
        <Stack>
          {mutation.isError && <Alert color="red">{mutation.error.message}</Alert>}
          <TextInput
            label="Usuario"
            placeholder="usuario@ejemplo.com"
            required
            {...form.getInputProps("login")}
          />
          <PasswordInput
            label={editing ? "Nueva contraseña (dejar en blanco para no cambiarla)" : "Contraseña"}
            required={!editing}
            {...form.getInputProps("password")}
          />
          <Group justify="flex-end">
            <Button variant="default" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" loading={mutation.isPending}>
              Guardar
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}
