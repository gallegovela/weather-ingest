import { Alert, Button, Group, Modal, Stack, Text, TextInput } from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { updateConfigValue } from "./configApi";

// Edit form for a single config_values row (spec/control/module/config.md):
// key/description are read-only, only value can be changed. For a
// `secret`-typed key the field starts empty rather than pre-filled with
// the masked placeholder the list shows -- submitting a blank value would
// just fail validation (value can't be empty), not silently keep the mask.
export function ValueForm({ opened, configValue, onClose }) {
  const queryClient = useQueryClient();

  const form = useForm({ initialValues: { value: "" } });

  useEffect(() => {
    if (opened) {
      form.setValues({ value: configValue?.value_type === "secret" ? "" : configValue?.value ?? "" });
      form.clearErrors();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, configValue]);

  const mutation = useMutation({
    mutationFn: (values) => updateConfigValue(configValue.key, values.value),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["config", "values"] });
      onClose();
    },
  });

  if (!configValue) return null;

  return (
    <Modal opened={opened} onClose={onClose} title={`Editar ${configValue.key}`}>
      <form onSubmit={form.onSubmit((values) => mutation.mutate(values))}>
        <Stack>
          {mutation.isError && <Alert color="red">{mutation.error.message}</Alert>}
          <Text size="sm" c="dimmed">
            {configValue.description}
          </Text>
          <TextInput
            label="Valor"
            required
            placeholder={configValue.value_type === "secret" ? "Nuevo valor (no se muestra el actual)" : undefined}
            {...form.getInputProps("value")}
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
