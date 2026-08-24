import { useQuery } from "@tanstack/react-query";

import { apiClient } from "./apiClient";

// Cross-cutting session guard (spec/control/core.md, "Authentication"):
// validity is checked against GET /api/security/session, which uses
// the same get_current_user dependency protecting the rest of the
// endpoints.
export function useSessionQuery() {
  return useQuery({
    queryKey: ["session"],
    queryFn: () => apiClient.get("/security/session"),
    retry: false,
  });
}
