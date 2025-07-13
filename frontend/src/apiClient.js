// src/apiClient.js
let endpoints = null;

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const apiUrl = (path) =>
  path.startsWith("http") ? path : `${BACKEND_URL}${path.startsWith("/") ? "" : "/"}${path}`;

// Endpoint registry
export async function loadEndpoints() {
  // Correct: matches backend @app.route('/api/registry')
  const response = await fetch(apiUrl("/api/registry"));
  if (!response.ok) throw new Error("Failed to load endpoint registry: " + response.status);
  return response.json();
}

// Dynamic endpoint loader
export async function getEndpoints() {
  if (endpoints) return endpoints;
  endpoints = await loadEndpoints();
  return endpoints;
}

// Generic API fetcher using endpoint registry
export async function apiFetch(endpointKey, options = {}) {
  // Ensure endpoints are loaded
  if (!endpoints) {
    endpoints = await loadEndpoints();
  }
  const endpointPath = endpoints[endpointKey];
  if (!endpointPath) {
    throw new Error(`Endpoint '${endpointKey}' not found in registry.`);
  }
  const url = apiUrl(endpointPath);
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`API call to '${endpointKey}' failed: ${response.status}`);
  }
  return response.json();
}

// Example for chat endpoint
export async function chatApi(data) {
  // Correct: matches backend @app.route('/api/chat')
  const response = await fetch(apiUrl("/api/chat"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return response.json();
}

// ...repeat for other endpoints...
