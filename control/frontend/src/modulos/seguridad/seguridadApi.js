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

export function listarUsuarios(params) {
  return apiClient.get(`/seguridad/usuarios?${aQueryString(params)}`);
}

export function crearUsuario(datos) {
  return apiClient.post("/seguridad/usuarios", datos);
}

export function editarUsuario(id, datos) {
  return apiClient.put(`/seguridad/usuarios/${id}`, datos);
}

export function eliminarUsuario(id) {
  return apiClient.delete(`/seguridad/usuarios/${id}`);
}
