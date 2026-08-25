import { Alert, Box, Collapse, Grid, NumberInput, Table, Text, TextInput, Title, UnstyledButton } from "@mantine/core";
import { DateInput } from "@mantine/dates";
import { useDebouncedValue } from "@mantine/hooks";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useSearchParams } from "react-router-dom";

import { Pagination } from "../../app/Pagination";
import { useVisibleColumns } from "../../app/useVisibleColumns";
import { ALWAYS_VISIBLE_FIELDS, FILTERABLE_FIELDS, OPTIONAL_FIELDS, formatValue } from "./columns";
import { listClimatologicalValues } from "./climatologicalValuesApi";

const PAGE_SIZE = 20;

function ValueRow({ value, visibleColumns, hiddenColumns }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <>
      <Table.Tr>
        <Table.Td>
          {hiddenColumns.length > 0 && (
            <UnstyledButton onClick={() => setExpanded((v) => !v)} aria-label="Expandir fila">
              {expanded ? "−" : "+"}
            </UnstyledButton>
          )}
        </Table.Td>
        {ALWAYS_VISIBLE_FIELDS.map((field) => (
          <Table.Td key={field.key}>{formatValue(field, value[field.key])}</Table.Td>
        ))}
        {visibleColumns.map((field) => (
          <Table.Td key={field.key}>{formatValue(field, value[field.key])}</Table.Td>
        ))}
      </Table.Tr>
      {hiddenColumns.length > 0 && (
        <Table.Tr>
          <Table.Td colSpan={ALWAYS_VISIBLE_FIELDS.length + 1 + visibleColumns.length} p={0}>
            <Collapse expanded={expanded}>
              <Box p="sm" bg="gray.0">
                <Grid>
                  {hiddenColumns.map((field) => (
                    <Grid.Col span={{ base: 12, sm: 6, md: 4 }} key={field.key}>
                      <Text size="sm" c="dimmed" span>
                        {field.label}:{" "}
                      </Text>
                      <Text size="sm" span>
                        {formatValue(field, value[field.key])}
                      </Text>
                    </Grid.Col>
                  ))}
                </Grid>
              </Box>
            </Collapse>
          </Table.Td>
        </Table.Tr>
      )}
    </>
  );
}

export function ValuesList() {
  const [searchParams] = useSearchParams();

  const [page, setPage] = useState(1);
  const [textFilters, setTextFilters] = useState(() => {
    const initial = {};
    for (const field of FILTERABLE_FIELDS) {
      if (field.filterType === "text") initial[field.key] = "";
    }
    initial.station_code = searchParams.get("station_code") ?? "";
    return initial;
  });
  const [rangeFilters, setRangeFilters] = useState(() => {
    const initial = {};
    for (const field of FILTERABLE_FIELDS) {
      if (field.filterType === "number_range") {
        initial[`${field.key}_from`] = "";
        initial[`${field.key}_to`] = "";
      }
    }
    return initial;
  });
  const [dateFilters, setDateFilters] = useState(() => {
    const initial = {};
    for (const field of FILTERABLE_FIELDS) {
      if (field.filterType === "date_range") {
        initial[`${field.key}_from`] = null;
        initial[`${field.key}_to`] = null;
      }
    }
    return initial;
  });

  // Mantine's DateInput (v9) already hands back "YYYY-MM-DD" strings,
  // usable as query params as-is -- no .toISOString() conversion needed.
  const filters = { ...textFilters, ...rangeFilters, ...dateFilters };
  const [debouncedFilters] = useDebouncedValue(filters, 400);

  const { containerRef, visible, hidden } = useVisibleColumns(OPTIONAL_FIELDS);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["climatological-values", "list", page, debouncedFilters],
    queryFn: () => listClimatologicalValues({ page, page_size: PAGE_SIZE, ...debouncedFilters }),
    placeholderData: (previous) => previous,
  });

  function updateText(key, value) {
    setPage(1);
    setTextFilters((prev) => ({ ...prev, [key]: value }));
  }
  function updateRange(key, value) {
    setPage(1);
    setRangeFilters((prev) => ({ ...prev, [key]: value === "" ? "" : value }));
  }
  function updateDate(key, value) {
    setPage(1);
    setDateFilters((prev) => ({ ...prev, [key]: value }));
  }

  return (
    <>
      <Title order={2} mb="md">Valores Diarios</Title>

      <Grid mb="md">
        {FILTERABLE_FIELDS.filter((f) => f.filterType === "text").map((field) => (
          <Grid.Col span={{ base: 12, sm: 4, md: 3 }} key={field.key}>
            <TextInput
              label={field.label}
              value={textFilters[field.key]}
              onChange={(e) => updateText(field.key, e.currentTarget.value)}
            />
          </Grid.Col>
        ))}
        {FILTERABLE_FIELDS.filter((f) => f.filterType === "number_range").flatMap((field) => [
          <Grid.Col span={{ base: 6, sm: 4, md: 3 }} key={`${field.key}_from`}>
            <NumberInput
              label={`${field.label} desde`}
              value={rangeFilters[`${field.key}_from`]}
              onChange={(v) => updateRange(`${field.key}_from`, v)}
            />
          </Grid.Col>,
          <Grid.Col span={{ base: 6, sm: 4, md: 3 }} key={`${field.key}_to`}>
            <NumberInput
              label={`${field.label} hasta`}
              value={rangeFilters[`${field.key}_to`]}
              onChange={(v) => updateRange(`${field.key}_to`, v)}
            />
          </Grid.Col>,
        ])}
        {FILTERABLE_FIELDS.filter((f) => f.filterType === "date_range").flatMap((field) => [
          <Grid.Col span={{ base: 6, sm: 4, md: 3 }} key={`${field.key}_from`}>
            <DateInput
              label={`${field.label} desde`}
              value={dateFilters[`${field.key}_from`]}
              onChange={(v) => updateDate(`${field.key}_from`, v)}
              clearable
            />
          </Grid.Col>,
          <Grid.Col span={{ base: 6, sm: 4, md: 3 }} key={`${field.key}_to`}>
            <DateInput
              label={`${field.label} hasta`}
              value={dateFilters[`${field.key}_to`]}
              onChange={(v) => updateDate(`${field.key}_to`, v)}
              clearable
            />
          </Grid.Col>,
        ])}
      </Grid>

      {isError && <Alert color="red">No se ha podido cargar el listado de valores diarios.</Alert>}

      <Box ref={containerRef}>
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th w={36} />
              {ALWAYS_VISIBLE_FIELDS.map((field) => (
                <Table.Th key={field.key}>{field.label}</Table.Th>
              ))}
              {visible.map((field) => (
                <Table.Th key={field.key}>{field.label}</Table.Th>
              ))}
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {data?.items.map((value) => (
              <ValueRow
                key={`${value.station_code}-${value.date}`}
                value={value}
                visibleColumns={visible}
                hiddenColumns={hidden}
              />
            ))}
          </Table.Tbody>
        </Table>
      </Box>

      {!isLoading && data && (
        <Pagination page={page} pageSize={PAGE_SIZE} total={data.total} onPageChange={setPage} />
      )}
    </>
  );
}
