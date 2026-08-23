import { useQuery } from "@tanstack/react-query";

import { apiClient } from "./apiClient";

// Guard de sesión transversal (spec/control/core.md, "Autenticación"):
// la validez se comprueba contra GET /api/seguridad/sesion, que usa la
// misma dependencia usuario_actual que protege el resto de endpoints.
export function useSesionQuery() {
  return useQuery({
    queryKey: ["sesion"],
    queryFn: () => apiClient.get("/seguridad/sesion"),
    retry: false,
  });
}
