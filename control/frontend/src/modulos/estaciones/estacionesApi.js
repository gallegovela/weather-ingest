import { apiClient } from "../../app/apiClient";

function aQueryString(params) {
  const query = new URLSearchParams();
  for (const [clave, valor] of Object.entries(params)) {
    if (valor !== undefined && valor !== null && valor !== "") {
      query.set(clave, valor);
    }
  }
  return query.toString();
}

export function listarEstaciones(params) {
  return apiClient.get(`/estaciones/estaciones?${aQueryString(params)}`);
}
