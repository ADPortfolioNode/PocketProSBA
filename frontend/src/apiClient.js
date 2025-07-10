// src/apiClient.js
let endpoints = null;

export async function loadEndpoints() {
  const backendUrl = process.env.REACT_APP_BACKEND_URL;
  if (!backendUrl) throw new Error("REACT_APP_BACKEND_URL is not set");
  const res = await fetch(`${backendUrl}/api`);
  if (!res.ok) throw new Error(`Failed to load endpoint registry: ${res.status}`);
  const data = await res.json();
  endpoints = data.endpoints;
  return endpoints;
}

export function getEndpoints() {
  if (!endpoints) throw new Error("Endpoints not loaded yet");
  return endpoints;
}

export async function apiFetch(pathKey, options = {}) {
  if (!endpoints) throw new Error("Endpoints not loaded yet");
  const backendUrl = process.env.REACT_APP_BACKEND_URL;
  if (!backendUrl) throw new Error("REACT_APP_BACKEND_URL is not set");
  const url = `${backendUrl}${endpoints[pathKey]}`;
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
