// Definición de columnas de la tabla `estaciones` (spec/db/tables.md) y de
// su tipo de filtro (spec/control/core.md, "Listados paginados con
// filtros"), compartida entre el listado y el detalle del mapa
// (spec/control/module/estaciones.md: "los mismos campos que en el
// listado"). `prioridad: 0` son las columnas que nunca se ocultan
// (indicativo, nombre, provincia — decidido en la spec).

function formatearFecha(valor) {
  return valor ? new Date(valor).toLocaleString() : "";
}

export const CAMPOS_ESTACION = [
  { clave: "indicativo", etiqueta: "Indicativo", tipoFiltro: "texto", prioridad: 0 },
  { clave: "nombre", etiqueta: "Nombre", tipoFiltro: "texto", prioridad: 0 },
  { clave: "provincia", etiqueta: "Provincia", tipoFiltro: "texto", prioridad: 0 },
  { clave: "altitud", etiqueta: "Altitud (m)", tipoFiltro: "rango_numero", prioridad: 1 },
  { clave: "indsinop", etiqueta: "Ind. sinóptico", tipoFiltro: "texto", prioridad: 2 },
  {
    clave: "latitud_decimal",
    etiqueta: "Latitud",
    tipoFiltro: "rango_numero",
    prioridad: 2,
  },
  {
    clave: "longitud_decimal",
    etiqueta: "Longitud",
    tipoFiltro: "rango_numero",
    prioridad: 2,
  },
  { clave: "latitud", etiqueta: "Latitud (GGMMSSH)", tipoFiltro: "texto", prioridad: 3 },
  { clave: "longitud", etiqueta: "Longitud (GGGMMSSH)", tipoFiltro: "texto", prioridad: 3 },
  {
    clave: "fecha_alta",
    etiqueta: "Fecha de alta",
    tipoFiltro: "rango_fecha",
    prioridad: 4,
    formatear: formatearFecha,
  },
  {
    clave: "fecha_actualizacion",
    etiqueta: "Última actualización",
    tipoFiltro: "rango_fecha",
    prioridad: 4,
    formatear: formatearFecha,
  },
];

export const CAMPOS_SIEMPRE_VISIBLES = CAMPOS_ESTACION.filter((c) => c.prioridad === 0);
export const CAMPOS_OPCIONALES = CAMPOS_ESTACION.filter((c) => c.prioridad > 0).sort(
  (a, b) => a.prioridad - b.prioridad,
);

export function formatearValor(campo, valor) {
  if (valor === null || valor === undefined) return "";
  return campo.formatear ? campo.formatear(valor) : String(valor);
}
