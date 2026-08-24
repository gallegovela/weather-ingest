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

export function listUsers(params) {
  return apiClient.get(`/security/users?${toQueryString(params)}`);
}

export function createUser(data) {
  return apiClient.post("/security/users", data);
}

export function updateUser(id, data) {
  return apiClient.put(`/security/users/${id}`, data);
}

export function deleteUser(id) {
  return apiClient.delete(`/security/users/${id}`);
}
