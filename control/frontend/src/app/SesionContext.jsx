import { createContext, useContext } from "react";

// Datos de la sesión actual ({ id, login }), resueltos una vez por
// RequireAuth y compartidos con Layout y las pantallas de cada módulo
// (ej. para ocultar "eliminar" sobre el propio usuario logado).
export const SesionContext = createContext(null);

export function useSesionActual() {
  return useContext(SesionContext);
}
