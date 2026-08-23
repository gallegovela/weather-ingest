import { Alert, Stack, Table, Title } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import L from "leaflet";
import iconRetina from "leaflet/dist/images/marker-icon-2x.png";
import icon from "leaflet/dist/images/marker-icon.png";
import iconShadow from "leaflet/dist/images/marker-shadow.png";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";

import { CAMPOS_ESTACION, formatearValor } from "./columnas";
import { listarEstaciones } from "./estacionesApi";

// Vite no resuelve los iconos por defecto de Leaflet al empaquetar; se
// reconfiguran explícitamente con las URLs importadas como assets.
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({ iconRetinaUrl: iconRetina, iconUrl: icon, shadowUrl: iconShadow });

// Centro aproximado de España, zoom pensado para ver toda la península
// + Baleares/Canarias a grandes rasgos al cargar el mapa.
const CENTRO_ESPANA = [40.0, -3.7];
const ZOOM_INICIAL = 6;

// El mapa reutiliza el mismo endpoint que el listado, pidiendo un
// tamaño de página que cubre de sobra las ~921 estaciones actuales en
// vez de paginar (decidido en spec/control/module/estaciones.md).
const TAMANO_PAGINA_MAPA = 2000;

export function Mapa() {
  const { data, isError } = useQuery({
    queryKey: ["estaciones", "mapa"],
    queryFn: () => listarEstaciones({ tamano_pagina: TAMANO_PAGINA_MAPA }),
  });

  return (
    <Stack h="100%" gap="md">
      <Title order={2}>Mapa de estaciones</Title>
      {isError && <Alert color="red">No se han podido cargar las estaciones.</Alert>}
      <MapContainer center={CENTRO_ESPANA} zoom={ZOOM_INICIAL} style={{ height: "75vh", width: "100%" }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MarkerClusterGroup chunkedLoading>
          {data?.items.map((estacion) => (
            <Marker
              key={estacion.indicativo}
              position={[Number(estacion.latitud_decimal), Number(estacion.longitud_decimal)]}
            >
              <Popup>
                <Table>
                  <Table.Tbody>
                    {CAMPOS_ESTACION.map((campo) => (
                      <Table.Tr key={campo.clave}>
                        <Table.Td>{campo.etiqueta}</Table.Td>
                        <Table.Td>{formatearValor(campo, estacion[campo.clave])}</Table.Td>
                      </Table.Tr>
                    ))}
                  </Table.Tbody>
                </Table>
              </Popup>
            </Marker>
          ))}
        </MarkerClusterGroup>
      </MapContainer>
    </Stack>
  );
}
