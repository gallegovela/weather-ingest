import { Navigate, Route, Routes } from "react-router-dom";

import { Layout } from "./app/Layout";
import { Login } from "./app/Login";
import { RequireAuth } from "./app/RequireAuth";
import { Map as StationsMap } from "./modules/stations/Map";
import { List as StationsList } from "./modules/stations/List";
import { UsersList } from "./modules/security/UsersList";
import { Stations as StationsJobs } from "./modules/jobs/Stations";
import { DailyValues as DailyValuesJobs } from "./modules/jobs/DailyValues";
import { ValuesList as ConfigValuesList } from "./modules/config/ValuesList";
import { ValuesList as ClimatologicalValuesList } from "./modules/climatological_values/ValuesList";
import { DailyValuesChart } from "./modules/climatological_values/DailyValuesChart";

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
          <Route path="/jobs/stations" element={<StationsJobs />} />
          <Route path="/jobs/daily-values" element={<DailyValuesJobs />} />
          <Route path="/config/values" element={<ConfigValuesList />} />
          <Route path="/climatological-values/values" element={<ClimatologicalValuesList />} />
          <Route path="/climatological-values/chart" element={<DailyValuesChart />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
