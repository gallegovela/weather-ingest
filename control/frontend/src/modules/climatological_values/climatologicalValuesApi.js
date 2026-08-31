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

export function listClimatologicalValues(params) {
  return apiClient.get(`/climatological-values/values?${toQueryString(params)}`);
}

export function getClimatologicalValuesYears(params) {
  return apiClient.get(`/climatological-values/years?${toQueryString(params)}`);
}

export function getClimatologicalValuesMonthlyCounts(params) {
  return apiClient.get(`/climatological-values/monthly-counts?${toQueryString(params)}`);
}
