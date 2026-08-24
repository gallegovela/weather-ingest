import { Group, Pagination as MantinePagination, Text } from "@mantine/core";

// Pagination control reused by every listing screen in the panel
// (cross-cutting "Paginated listings with filters" convention,
// spec/control/core.md).
export function Pagination({ page, pageSize, total, onPageChange }) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <Group justify="space-between" mt="md">
      <Text size="sm" c="dimmed">
        {total} resultado{total === 1 ? "" : "s"}
      </Text>
      <MantinePagination value={page} onChange={onPageChange} total={totalPages} />
    </Group>
  );
}
