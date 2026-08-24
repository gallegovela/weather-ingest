import { apiClient } from "../../app/apiClient";

export function listConfigValues() {
  return apiClient.get("/config/values");
}

export function updateConfigValue(key, value) {
  return apiClient.put(`/config/values/${key}`, { value });
}
