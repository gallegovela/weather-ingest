import { Alert, Box, Collapse, Grid, NumberInput, Table, Text, TextInput, Title, UnstyledButton } from "@mantine/core";
import { DateInput } from "@mantine/dates";
import { useDebouncedValue } from "@mantine/hooks";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { Paginacion } from "../../app/Paginacion";
import { CAMPOS_OPCIONALES, CAMPOS_SIEMPRE_VISIBLES, formatearValor } from "./columnas";
import { listarEstaciones } from "./estacionesApi";
import { useColumnasVisibles } from "./useColumnasVisibles";

const TAMANO_PAGINA = 20;
const FECHA_ISO = (fecha) => fecha?.toISOString().slice(0, 10);

function FilaEstacion({ estacion, columnasVisibles, columnasOcultas }) {
  const [expandida, setExpandida] = useState(false);

  return (
    <>
      <Table.Tr>
        <Table.Td>
          {columnasOcultas.length > 0 && (
            <UnstyledButton onClick={() => setExpandida((v) => !v)} aria-label="Expandir fila">
              {expandida ? "−" : "+"}
            </UnstyledButton>
          )}
        </Table.Td>
        {CAMPOS_SIEMPRE_VISIBLES.map((campo) => (
          <Table.Td key={campo.clave}>{formatearValor(campo, estacion[campo.clave])}</Table.Td>
        ))}
        {columnasVisibles.map((campo) => (
          <Table.Td key={campo.clave}>{formatearValor(campo, estacion[campo.clave])}</Table.Td>
        ))}
      </Table.Tr>
      {columnasOcultas.length > 0 && (
        <Table.Tr>
          <Table.Td colSpan={CAMPOS_SIEMPRE_VISIBLES.length + 1} p={0}>
            <Collapse in={expandida}>
              <Box p="sm" bg="gray.0">
                <Grid>
                  {columnasOcultas.map((campo) => (
                    <Grid.Col span={{ base: 12, sm: 6, md: 4 }} key={campo.clave}>
                      <Text size="sm" c="dimmed" span>
                        {campo.etiqueta}:{" "}
                      </Text>
                      <Text size="sm" span>
                        {formatearValor(campo, estacion[campo.clave])}
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

export function Listado() {
  const [pagina, setPagina] = useState(1);
  const [filtrosTexto, setFiltrosTexto] = useState({
    indicativo: "", nombre: "", provincia: "", indsinop: "", latitud: "", longitud: "",
  });
  const [filtrosRango, setFiltrosRango] = useState({
    altitud_desde: "", altitud_hasta: "",
    latitud_decimal_desde: "", latitud_decimal_hasta: "",
    longitud_decimal_desde: "", longitud_decimal_hasta: "",
  });
  const [fechas, setFechas] = useState({
    fecha_alta_desde: null, fecha_alta_hasta: null,
    fecha_actualizacion_desde: null, fecha_actualizacion_hasta: null,
  });

  const filtros = {
    ...filtrosTexto,
    ...filtrosRango,
    fecha_alta_desde: FECHA_ISO(fechas.fecha_alta_desde),
    fecha_alta_hasta: FECHA_ISO(fechas.fecha_alta_hasta),
    fecha_actualizacion_desde: FECHA_ISO(fechas.fecha_actualizacion_desde),
    fecha_actualizacion_hasta: FECHA_ISO(fechas.fecha_actualizacion_hasta),
  };
  const [filtrosDebounced] = useDebouncedValue(filtros, 400);

  const { contenedorRef, visibles, ocultas } = useColumnasVisibles(CAMPOS_OPCIONALES);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["estaciones", "listado", pagina, filtrosDebounced],
    queryFn: () => listarEstaciones({ pagina, tamano_pagina: TAMANO_PAGINA, ...filtrosDebounced }),
    placeholderData: (anterior) => anterior,
  });

  function actualizarTexto(clave, valor) {
    setPagina(1);
    setFiltrosTexto((prev) => ({ ...prev, [clave]: valor }));
  }
  function actualizarRango(clave, valor) {
    setPagina(1);
    setFiltrosRango((prev) => ({ ...prev, [clave]: valor === "" ? "" : valor }));
  }
  function actualizarFecha(clave, valor) {
    setPagina(1);
    setFechas((prev) => ({ ...prev, [clave]: valor }));
  }

  return (
    <>
      <Title order={2} mb="md">Estaciones</Title>

      <Grid mb="md">
        <Grid.Col span={{ base: 12, sm: 4, md: 3 }}>
          <TextInput label="Indicativo" value={filtrosTexto.indicativo} onChange={(e) => actualizarTexto("indicativo", e.currentTarget.value)} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 4, md: 3 }}>
          <TextInput label="Nombre" value={filtrosTexto.nombre} onChange={(e) => actualizarTexto("nombre", e.currentTarget.value)} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 4, md: 3 }}>
          <TextInput label="Provincia" value={filtrosTexto.provincia} onChange={(e) => actualizarTexto("provincia", e.currentTarget.value)} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 4, md: 3 }}>
          <TextInput label="Ind. sinóptico" value={filtrosTexto.indsinop} onChange={(e) => actualizarTexto("indsinop", e.currentTarget.value)} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 4, md: 3 }}>
          <TextInput label="Latitud (GGMMSSH)" value={filtrosTexto.latitud} onChange={(e) => actualizarTexto("latitud", e.currentTarget.value)} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 4, md: 3 }}>
          <TextInput label="Longitud (GGGMMSSH)" value={filtrosTexto.longitud} onChange={(e) => actualizarTexto("longitud", e.currentTarget.value)} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
          <NumberInput label="Altitud desde" value={filtrosRango.altitud_desde} onChange={(v) => actualizarRango("altitud_desde", v)} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
          <NumberInput label="Altitud hasta" value={filtrosRango.altitud_hasta} onChange={(v) => actualizarRango("altitud_hasta", v)} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
          <NumberInput label="Latitud desde" decimalScale={6} value={filtrosRango.latitud_decimal_desde} onChange={(v) => actualizarRango("latitud_decimal_desde", v)} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
          <NumberInput label="Latitud hasta" decimalScale={6} value={filtrosRango.latitud_decimal_hasta} onChange={(v) => actualizarRango("latitud_decimal_hasta", v)} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
          <NumberInput label="Longitud desde" decimalScale={6} value={filtrosRango.longitud_decimal_desde} onChange={(v) => actualizarRango("longitud_decimal_desde", v)} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
          <NumberInput label="Longitud hasta" decimalScale={6} value={filtrosRango.longitud_decimal_hasta} onChange={(v) => actualizarRango("longitud_decimal_hasta", v)} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
          <DateInput label="Alta desde" value={fechas.fecha_alta_desde} onChange={(v) => actualizarFecha("fecha_alta_desde", v)} clearable />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
          <DateInput label="Alta hasta" value={fechas.fecha_alta_hasta} onChange={(v) => actualizarFecha("fecha_alta_hasta", v)} clearable />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
          <DateInput label="Actualización desde" value={fechas.fecha_actualizacion_desde} onChange={(v) => actualizarFecha("fecha_actualizacion_desde", v)} clearable />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
          <DateInput label="Actualización hasta" value={fechas.fecha_actualizacion_hasta} onChange={(v) => actualizarFecha("fecha_actualizacion_hasta", v)} clearable />
        </Grid.Col>
      </Grid>

      {isError && <Alert color="red">No se ha podido cargar el listado de estaciones.</Alert>}

      <Box ref={contenedorRef}>
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th w={36} />
              {CAMPOS_SIEMPRE_VISIBLES.map((campo) => (
                <Table.Th key={campo.clave}>{campo.etiqueta}</Table.Th>
              ))}
              {visibles.map((campo) => (
                <Table.Th key={campo.clave}>{campo.etiqueta}</Table.Th>
              ))}
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {data?.items.map((estacion) => (
              <FilaEstacion
                key={estacion.indicativo}
                estacion={estacion}
                columnasVisibles={visibles}
                columnasOcultas={ocultas}
              />
            ))}
          </Table.Tbody>
        </Table>
      </Box>

      {!isLoading && data && (
        <Paginacion pagina={pagina} tamanoPagina={TAMANO_PAGINA} total={data.total} onCambiarPagina={setPagina} />
      )}
    </>
  );
}
