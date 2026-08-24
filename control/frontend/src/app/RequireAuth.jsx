import { Center, Loader } from "@mantine/core";
import { Navigate, Outlet, useLocation } from "react-router-dom";

import { SessionContext } from "./SessionContext";
import { useSessionQuery } from "./useSessionQuery";

// Cross-cutting session guard (spec/control/core.md, "Authentication"):
// without a valid session no panel route is accessible.
export function RequireAuth() {
  const location = useLocation();
  const { data, isLoading, isError } = useSessionQuery();

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
    <SessionContext.Provider value={data}>
      <Outlet />
    </SessionContext.Provider>
  );
}
