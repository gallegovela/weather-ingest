import { Center, Loader } from "@mantine/core";
import { Navigate, Outlet, useLocation } from "react-router-dom";

import { SesionContext } from "./SesionContext";
import { useSesionQuery } from "./useSesionQuery";

// Guard de sesión transversal (spec/control/core.md, "Autenticación"):
// sin sesión válida no se accede a ninguna ruta del panel.
export function RequireAuth() {
  const location = useLocation();
  const { data, isLoading, isError } = useSesionQuery();

  if (isLoading) {
    return (
      <Center h="100vh">
        <Loader />
      </Center>
    );
  }

  if (isError) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return (
    <SesionContext.Provider value={data}>
      <Outlet />
    </SesionContext.Provider>
  );
}
