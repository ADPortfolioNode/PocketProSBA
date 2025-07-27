// src/apiClient.js
let endpoints = null;

const BACKEND_URL = process.env.REACT_APP_API_BASE || process.env.REACT_APP_BACKEND_URL || "http://localhost:5000";
const apiUrl = (path) =>
  path.startsWith("http") ? path : `${BACKEND_URL}${path.startsWith("/") ? "" : "/"}${path}`;

// Centralized fetch wrapper with error handling
async function fetchWithErrorHandling(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Fetch error: ${response.status} ${response.statusText} - ${errorText}`);
  }
  return response.json();
}

// Endpoint registry
export async function loadEndpoints() {
  // Correct: matches backend @app.route('/api/registry')
  return fetchWithErrorHandling(apiUrl("/api/registry"));
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
  return fetchWithErrorHandling(url, options);
}

// Example for chat endpoint
export async function chatApi(data) {
  // Correct: matches backend @app.route('/api/chat')
  return fetchWithErrorHandling(apiUrl("/api/chat"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

// Health check endpoint
export async function healthCheck() {
  return fetchWithErrorHandling(apiUrl("/api/health"));
}

// Add other API endpoint functions here as needed
