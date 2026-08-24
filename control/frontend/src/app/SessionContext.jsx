import { createContext, useContext } from "react";

// Current session data ({ id, login }), resolved once by RequireAuth
// and shared with Layout and each module's screens (e.g. to hide
// "delete" on the currently logged-in user).
export const SessionContext = createContext(null);

export function useCurrentSession() {
  return useContext(SessionContext);
}
