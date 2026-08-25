import { Alert, Stack, Table, Title } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import L from "leaflet";
import iconRetina from "leaflet/dist/images/marker-icon-2x.png";
import icon from "leaflet/dist/images/marker-icon.png";
import iconShadow from "leaflet/dist/images/marker-shadow.png";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
// Cluster icon styles (the colored circle + count) -- without these,
// clusters render as bare unstyled numbers. Not pulled in by
// react-leaflet-cluster or leaflet/dist/leaflet.css automatically.
import "react-leaflet-cluster/dist/assets/MarkerCluster.css";
import "react-leaflet-cluster/dist/assets/MarkerCluster.Default.css";

import { STATION_FIELDS, formatValue } from "./columns";
import { listStations } from "./stationsApi";

// Vite doesn't resolve Leaflet's default icons when bundling; they're
// explicitly reconfigured with the URLs imported as assets.
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({ iconRetinaUrl: iconRetina, iconUrl: icon, shadowUrl: iconShadow });

// Approximate center of Spain, zoom chosen to roughly see the whole
// peninsula + Balearic/Canary Islands when the map loads.
const SPAIN_CENTER = [40.0, -3.7];
const INITIAL_ZOOM = 6;

// The map reuses the same endpoint as the listing, requesting a page
// size that comfortably covers the ~921 current stations instead of
// paginating (decided in spec/control/module/stations.md).
const MAP_PAGE_SIZE = 2000;

export function Map() {
  const { data, isError } = useQuery({
    queryKey: ["stations", "map"],
    queryFn: () => listStations({ page_size: MAP_PAGE_SIZE }),
  });

  return (
    <Stack h="100%" gap="md">
      <Title order={2}>Mapa de estaciones</Title>
      {isError && <Alert color="red">No se han podido cargar las estaciones.</Alert>}
      <MapContainer center={SPAIN_CENTER} zoom={INITIAL_ZOOM} style={{ height: "75vh", width: "100%" }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MarkerClusterGroup chunkedLoading>
          {data?.items.map((station) => (
            <Marker
              key={station.station_code}
              position={[Number(station.latitude_decimal), Number(station.longitude_decimal)]}
            >
              {/* autoPan disabled: on mobile, the pan it triggers can land the
                  marker back inside a cluster's recompute radius, which makes
                  MarkerClusterGroup re-render it away and the popup closes
                  itself right after opening. */}
              <Popup autoPan={false}>
                <Table>
                  <Table.Tbody>
                    {STATION_FIELDS.map((field) => (
                      <Table.Tr key={field.key}>
                        <Table.Td>{field.label}</Table.Td>
                        <Table.Td>{formatValue(field, station[field.key])}</Table.Td>
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
