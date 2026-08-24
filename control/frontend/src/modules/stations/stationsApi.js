import { apiClient } from "../../app/apiClient";

function toQueryString(params) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, value);
    }
  }
  return query.toString();
}

export function listStations(params) {
  return apiClient.get(`/stations/stations?${toQueryString(params)}`);
}
