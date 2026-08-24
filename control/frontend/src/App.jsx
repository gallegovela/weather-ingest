import { Navigate, Route, Routes } from "react-router-dom";

import { Layout } from "./app/Layout";
import { Login } from "./app/Login";
import { RequireAuth } from "./app/RequireAuth";
import { Map as StationsMap } from "./modules/stations/Map";
import { List as StationsList } from "./modules/stations/List";
import { UsersList } from "./modules/security/UsersList";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route element={<RequireAuth />}>
        <Route element={<Layout />}>
          <Route index element={<Navigate to="/stations/list" replace />} />
          <Route path="/stations/list" element={<StationsList />} />
          <Route path="/stations/map" element={<StationsMap />} />
          <Route path="/security/users" element={<UsersList />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
