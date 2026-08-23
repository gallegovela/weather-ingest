// Cliente HTTP transversal: todas las llamadas de control/frontend/ a
// control/backend/ pasan por aquí. La sesión viaja en una cookie
// httpOnly (ver spec/control/core.md, "Autenticación"), de ahí
// `credentials: "include"` en cada petición.

const BASE_URL = "/api";

export class ApiError extends Error {
  constructor(status, detail) {
    super(detail || `Error ${status}`);
    this.status = status;
  }
}

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    credentials: "include",
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
    ...options,
  });

  if (res.status === 204) {
    return null;
  }

  const esJson = res.headers.get("content-type")?.includes("application/json");
  const datos = esJson ? await res.json() : null;

  if (!res.ok) {
    // Formato de error por defecto de FastAPI: {"detail": "mensaje"}
    // (ver spec/control/core.md, "Contrato de la API REST").
    throw new ApiError(res.status, datos?.detail);
  }

  return datos;
}

export const apiClient = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: "POST", body: JSON.stringify(body) }),
  put: (path, body) => request(path, { method: "PUT", body: JSON.stringify(body) }),
  delete: (path) => request(path, { method: "DELETE" }),
};
