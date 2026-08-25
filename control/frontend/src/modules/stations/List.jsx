import { Alert, Anchor, Box, Collapse, Grid, NumberInput, Table, Text, TextInput, Title, UnstyledButton } from "@mantine/core";
import { DateInput } from "@mantine/dates";
import { useDebouncedValue } from "@mantine/hooks";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { Pagination } from "../../app/Pagination";
import { useVisibleColumns } from "../../app/useVisibleColumns";
import { ALWAYS_VISIBLE_FIELDS, OPTIONAL_FIELDS, formatValue } from "./columns";
import { listStations } from "./stationsApi";

const PAGE_SIZE = 20;

function StationRow({ station, visibleColumns, hiddenColumns }) {
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
          <Table.Td key={field.key}>{formatValue(field, station[field.key])}</Table.Td>
        ))}
        {visibleColumns.map((field) => (
          <Table.Td key={field.key}>{formatValue(field, station[field.key])}</Table.Td>
        ))}
        <Table.Td>
          <Anchor
            component={Link}
            to={`/climatological-values/values?station_code=${station.station_code}`}
            size="sm"
          >
            Valores diarios
          </Anchor>
        </Table.Td>
      </Table.Tr>
      {hiddenColumns.length > 0 && (
        <Table.Tr>
          <Table.Td colSpan={ALWAYS_VISIBLE_FIELDS.length + 2 + visibleColumns.length} p={0}>
            <Collapse expanded={expanded}>
              <Box p="sm" bg="gray.0">
                <Grid>
                  {hiddenColumns.map((field) => (
                    <Grid.Col span={{ base: 12, sm: 6, md: 4 }} key={field.key}>
                      <Text size="sm" c="dimmed" span>
                        {field.label}:{" "}
                      </Text>
                      <Text size="sm" span>
                        {formatValue(field, station[field.key])}
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

export function List() {
  const [page, setPage] = useState(1);
  const [textFilters, setTextFilters] = useState({
    station_code: "", name: "", province: "", synoptic_code: "", latitude: "", longitude: "",
  });
  const [rangeFilters, setRangeFilters] = useState({
    altitude_from: "", altitude_to: "",
    latitude_decimal_from: "", latitude_decimal_to: "",
    longitude_decimal_from: "", longitude_decimal_to: "",
  });
  const [dates, setDates] = useState({
    created_at_from: null, created_at_to: null,
    updated_at_from: null, updated_at_to: null,
  });

  // Mantine's DateInput (v9) already hands back "YYYY-MM-DD" strings,
  // usable as query params as-is -- no .toISOString() conversion needed.
  const filters = {
    ...textFilters,
    ...rangeFilters,
    ...dates,
  };
  const [debouncedFilters] = useDebouncedValue(filters, 400);

  const { containerRef, visible, hidden } = useVisibleColumns(OPTIONAL_FIELDS);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["stations", "list", page, debouncedFilters],
    queryFn: () => listStations({ page, page_size: PAGE_SIZE, ...debouncedFilters }),
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
    setDates((prev) => ({ ...prev, [key]: value }));
  }

  return (
    <>
      <Title order={2} mb="md">Estaciones</Title>

      <Grid mb="md">
        <Grid.Col span={{ base: 12, sm: 4, md: 3 }}>
          <TextInput label="Indicativo" value={textFilters.station_code} onChange={(e) => updateText("station_code", e.currentTarget.value)} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 4, md: 3 }}>
          <TextInput label="Nombre" value={textFilters.name} onChange={(e) => updateText("name", e.currentTarget.value)} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 4, md: 3 }}>
          <TextInput label="Provincia" value={textFilters.province} onChange={(e) => updateText("province", e.currentTarget.value)} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 4, md: 3 }}>
          <TextInput label="Ind. sinóptico" value={textFilters.synoptic_code} onChange={(e) => updateText("synoptic_code", e.currentTarget.value)} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 4, md: 3 }}>
          <TextInput label="Latitud (GGMMSSH)" value={textFilters.latitude} onChange={(e) => updateText("latitude", e.currentTarget.value)} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 4, md: 3 }}>
          <TextInput label="Longitud (GGGMMSSH)" value={textFilters.longitude} onChange={(e) => updateText("longitude", e.currentTarget.value)} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
          <NumberInput label="Altitud desde" value={rangeFilters.altitude_from} onChange={(v) => updateRange("altitude_from", v)} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
          <NumberInput label="Altitud hasta" value={rangeFilters.altitude_to} onChange={(v) => updateRange("altitude_to", v)} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
          <NumberInput label="Latitud desde" decimalScale={6} value={rangeFilters.latitude_decimal_from} onChange={(v) => updateRange("latitude_decimal_from", v)} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
          <NumberInput label="Latitud hasta" decimalScale={6} value={rangeFilters.latitude_decimal_to} onChange={(v) => updateRange("latitude_decimal_to", v)} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
          <NumberInput label="Longitud desde" decimalScale={6} value={rangeFilters.longitude_decimal_from} onChange={(v) => updateRange("longitude_decimal_from", v)} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
          <NumberInput label="Longitud hasta" decimalScale={6} value={rangeFilters.longitude_decimal_to} onChange={(v) => updateRange("longitude_decimal_to", v)} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
          <DateInput label="Alta desde" value={dates.created_at_from} onChange={(v) => updateDate("created_at_from", v)} clearable />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
          <DateInput label="Alta hasta" value={dates.created_at_to} onChange={(v) => updateDate("created_at_to", v)} clearable />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
          <DateInput label="Actualización desde" value={dates.updated_at_from} onChange={(v) => updateDate("updated_at_from", v)} clearable />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
          <DateInput label="Actualización hasta" value={dates.updated_at_to} onChange={(v) => updateDate("updated_at_to", v)} clearable />
        </Grid.Col>
      </Grid>

      {isError && <Alert color="red">No se ha podido cargar el listado de estaciones.</Alert>}

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
              <Table.Th />
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {data?.items.map((station) => (
              <StationRow
                key={station.station_code}
                station={station}
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
