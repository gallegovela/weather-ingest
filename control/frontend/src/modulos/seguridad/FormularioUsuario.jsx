import { Alert, Button, Group, Modal, PasswordInput, Stack, TextInput } from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { crearUsuario, editarUsuario } from "./seguridadApi";

// Formulario de alta y edición de usuario (spec/control/module/seguridad.md,
// pantallas 3 y 4): un único componente reutilizado para ambas, según la
// organización fijada en spec/control/core.md.
export function FormularioUsuario({ opened, usuario, onClose }) {
  const editando = Boolean(usuario);
  const queryClient = useQueryClient();

  const form = useForm({
    initialValues: { login: "", contrasena: "" },
    validate: {
      login: (valor) => (/^\S+@\S+\.\S+$/.test(valor) ? null : "Formato de email no válido"),
      contrasena: (valor) => (!editando && !valor ? "La contraseña es obligatoria" : null),
    },
  });

  useEffect(() => {
    if (opened) {
      form.setValues({ login: usuario?.login ?? "", contrasena: "" });
      form.clearErrors();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, usuario]);

  const mutation = useMutation({
    mutationFn: (valores) => {
      const datos = { login: valores.login };
      if (valores.contrasena) datos.contrasena = valores.contrasena;
      return editando ? editarUsuario(usuario.id, datos) : crearUsuario({ ...datos, contrasena: valores.contrasena });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["usuarios"] });
      onClose();
    },
  });

  return (
    <Modal opened={opened} onClose={onClose} title={editando ? "Editar usuario" : "Añadir usuario"}>
      <form onSubmit={form.onSubmit((valores) => mutation.mutate(valores))}>
        <Stack>
          {mutation.isError && <Alert color="red">{mutation.error.message}</Alert>}
          <TextInput
            label="Usuario"
            placeholder="usuario@ejemplo.com"
            required
            {...form.getInputProps("login")}
          />
          <PasswordInput
            label={editando ? "Nueva contraseña (dejar en blanco para no cambiarla)" : "Contraseña"}
            required={!editando}
            {...form.getInputProps("contrasena")}
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
