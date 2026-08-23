import { Navigate, Route, Routes } from "react-router-dom";

import { Layout } from "./app/Layout";
import { Login } from "./app/Login";
import { RequireAuth } from "./app/RequireAuth";
import { Mapa as MapaEstaciones } from "./modulos/estaciones/Mapa";
import { Listado as ListadoEstaciones } from "./modulos/estaciones/Listado";
import { ListadoUsuarios } from "./modulos/seguridad/ListadoUsuarios";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route element={<RequireAuth />}>
        <Route element={<Layout />}>
          <Route index element={<Navigate to="/estaciones/listado" replace />} />
          <Route path="/estaciones/listado" element={<ListadoEstaciones />} />
          <Route path="/estaciones/mapa" element={<MapaEstaciones />} />
          <Route path="/seguridad/usuarios" element={<ListadoUsuarios />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
