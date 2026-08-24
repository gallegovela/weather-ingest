// Cross-cutting HTTP client: every call from control/frontend/ to
// control/backend/ goes through here. The session travels in an
// httpOnly cookie (see spec/control/core.md, "Authentication"), hence
// `credentials: "include"` on every request.

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

  const isJson = res.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await res.json() : null;

  if (!res.ok) {
    // FastAPI's default error format: {"detail": "message"}
    // (see spec/control/core.md, "REST API contract").
    throw new ApiError(res.status, data?.detail);
  }

  return data;
}

export const apiClient = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: "POST", body: JSON.stringify(body) }),
  put: (path, body) => request(path, { method: "PUT", body: JSON.stringify(body) }),
  delete: (path) => request(path, { method: "DELETE" }),
};
