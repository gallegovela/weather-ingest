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

export function createStationsJob() {
  return apiClient.post("/jobs/stations");
}

export function listStationsJobs(params) {
  return apiClient.get(`/jobs/stations?${toQueryString(params)}`);
}

export function cancelStationsJob(id) {
  return apiClient.post(`/jobs/stations/${id}/cancel`);
}

export function deleteStationsJobs(ids) {
  return apiClient.delete("/jobs/stations", { ids });
}

export function createDailyValuesJob(data) {
  return apiClient.post("/jobs/daily-values", data);
}

export function listDailyValuesJobs(params) {
  return apiClient.get(`/jobs/daily-values?${toQueryString(params)}`);
}

export function cancelDailyValuesJob(id) {
  return apiClient.post(`/jobs/daily-values/${id}/cancel`);
}

export function deleteDailyValuesJobs(ids) {
  return apiClient.delete("/jobs/daily-values", { ids });
}
