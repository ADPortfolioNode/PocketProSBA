import axios from 'axios';
import { clearSession, getToken, loginPathFor } from '../utils/authStorage';

const getBackendHost = () => {
  const envHost = process.env.REACT_APP_API_URL || process.env.REACT_APP_BACKEND_URL;

  const normalizeHost = (host) => {
    if (!host) return host;
    // Prefer IPv4 — Windows often maps localhost → ::1 (flaky via WSL/Docker relay)
    return host
      .replace(/\/api\/?$/, '')
      .replace(/\/+$/, '')
      .replace('://localhost', '://127.0.0.1');
  };

  if (typeof window === 'undefined') {
    return normalizeHost(envHost) || 'http://127.0.0.1:5000';
  }

  const params = new URLSearchParams(window.location.search);
  const backendHost = params.get('backend_host') || params.get('backendUrl') || params.get('api_host');
  if (backendHost) {
    return normalizeHost(backendHost);
  }

  if (envHost) {
    return normalizeHost(envHost);
  }

  // When UI is served from nginx :3000, use same-origin so /api is proxied (most reliable)
  const { protocol, hostname, port } = window.location;
  if (port === '3000' || hostname === 'localhost' || hostname === '127.0.0.1') {
    // Same origin when using frontend proxy; falls back work if absolute needed
    return `${protocol}//${hostname === 'localhost' ? '127.0.0.1' : hostname}${port ? `:${port}` : ''}`;
  }

  return `${protocol}//${hostname}${port ? `:${port}` : ''}`;
};

const BASE_URL = getBackendHost();
// Retry policy for transient failures (cold start, deploy, proxy hiccup).
// Retries back off 1s, 2s, 4s, 4s, 4s (~15s) and stop once RETRY_BUDGET_MS has
// passed, so a real outage surfaces as an error after ~15-20s, never instantly.
const MAX_RETRIES = 5;
const RETRY_DELAY = 1000;
const MAX_RETRY_DELAY = 4000;
const RETRY_BUDGET_MS = 20000;
const RETRYABLE_STATUS = [502, 503, 504];

/** True for failures worth retrying: no response (refused/reset/network) or a gateway 502/503/504. */
const isTransientError = (error, method = 'GET') => {
  if (!error || axios.isCancel?.(error)) return false;
  const status = error.response?.status;
  if (status) {
    // 504 may mean the backend did the work; don't replay non-idempotent calls.
    if (status === 504 && !['GET', 'HEAD', 'OPTIONS'].includes(String(method).toUpperCase())) return false;
    return RETRYABLE_STATUS.includes(status);
  }
  // Our own long timeout already exceeded the retry budget; don't stack another.
  if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT') return false;
  return ['ECONNREFUSED', 'ECONNRESET', 'ERR_NETWORK', 'EAI_AGAIN'].includes(error.code) || !!error.request || error.message === 'Network Error';
};

/* global globalThis */
// globalThis.__PP_RETRY_DELAY_MS__ lets the Jest setup shrink the back-off (setupTests.js).
const retryDelay = (attempt) => {
  const base = typeof globalThis.__PP_RETRY_DELAY_MS__ === 'number' ? globalThis.__PP_RETRY_DELAY_MS__ : RETRY_DELAY;
  return Math.min(base * 2 ** attempt, base ? MAX_RETRY_DELAY : 0);
};

const axiosInstance = axios.create({
  baseURL: BASE_URL,
  // SBA content can include live sba.gov scrapes — 10s was blanking Resources cards
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// --- Authentication -------------------------------------------------------
// Every request carries the stored access token as "Authorization: Bearer".
// A 401 from a protected route means the token is missing, expired or no longer
// valid: the session is cleared and the user is sent to /login with the page
// they were on as ?next=, so they come straight back after signing in.

// Auth endpoints answer 401 for a wrong password; that must not redirect.
const AUTH_ENDPOINT_RE = /\/api\/(auth\/|login|register|forgot-password|reset-password)/;

const defaultUnauthorizedHandler = (loginPath) => {
  if (typeof window !== 'undefined' && window.location) window.location.assign(loginPath);
};
let unauthorizedHandler = defaultUnauthorizedHandler;

/** App registers a router-aware handler (no full page reload); null restores the default. */
const setUnauthorizedHandler = (fn) => {
  unauthorizedHandler = typeof fn === 'function' ? fn : defaultUnauthorizedHandler;
};

const handleUnauthorized = (error) => {
  const url = String(error?.config?.url || '');
  if (error?.response?.status !== 401 || AUTH_ENDPOINT_RE.test(url)) return;
  clearSession();
  if (typeof window === 'undefined' || !window.location) return;
  const { pathname = '/', search = '', hash = '' } = window.location;
  if (/^\/login(\/|$)/i.test(pathname)) return;
  unauthorizedHandler(loginPathFor(`${pathname}${search}${hash}`));
};

axiosInstance.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers = config.headers || {};
    // An explicit Authorization passed by the caller wins.
    const has = typeof config.headers.has === 'function'
      ? config.headers.has('Authorization')
      : !!(config.headers.Authorization || config.headers.authorization);
    if (!has) {
      if (typeof config.headers.set === 'function') config.headers.set('Authorization', `Bearer ${token}`);
      else config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    handleUnauthorized(error);
    return Promise.reject(error);
  }
);

// Create the request handler
// options: { quiet } suppresses logging; { retry: false } disables retries;
// { retryBudgetMs } overrides the total time spent retrying.
const makeRequest = async (method, endpoint, data = null, config = {}, retries = MAX_RETRIES, options = {}) => {
  const { quiet = false, retry = true, retryBudgetMs = RETRY_BUDGET_MS } = options;
  const startedAt = options._startedAt || Date.now();
  const attempt = MAX_RETRIES - retries;

  try {
    if (!quiet) console.log('Making request to:', endpoint);
    const requestConfig = {
      method,
      url: endpoint,
      ...config
    };

    if (data !== null) {
      requestConfig.data = data;
    }

    const response = await axiosInstance(requestConfig);
    return response;
  } catch (error) {
    const delay = retryDelay(attempt);
    const withinBudget = Date.now() - startedAt + delay <= retryBudgetMs;
    if (retry && retries > 0 && withinBudget && isTransientError(error, method)) {
      if (!quiet) {
        console.log(`Retrying ${endpoint} in ${delay}ms (${retries} attempts left)`);
      }
      await new Promise(resolve => setTimeout(resolve, delay));
      return makeRequest(method, endpoint, data, config, retries - 1, { ...options, _startedAt: startedAt });
    }
    error.attempts = attempt + 1;
    if (!quiet) {
      console.error('API Error:', error);
    }
    throw error;
  }
};

// Define the endpoints
const endpointRegistry = {
  api_health: '/api/health',
  api_info: '/api/info',
  api_decompose: '/api/decompose',
  api_execute: '/api/execute',
  api_validate: '/api/validate',
  api_query: '/api/query',
  api_chat: '/api/chat',
  api_diagnostics: '/api/diagnostics'
};

// Create the API methods
const get = (endpoint, config = {}, options = {}) => makeRequest('GET', endpoint, null, config, MAX_RETRIES, options);
const post = (endpoint, data, config = {}, options = {}) => makeRequest('POST', endpoint, data, config, MAX_RETRIES, options);
const put = (endpoint, data, config = {}, options = {}) => makeRequest('PUT', endpoint, data, config, MAX_RETRIES, options);
const delete_ = (endpoint, config = {}, options = {}) => makeRequest('DELETE', endpoint, null, config, MAX_RETRIES, options);

// Helper function to load endpoints (used in tests)
const loadEndpoints = async () => ({
  endpoints: endpointRegistry,
  baseURL: axiosInstance.defaults.baseURL,
  timestamp: new Date().toISOString()
});

// Export a consistent API object
const api = {
  get,
  post,
  put,
  delete: delete_,
  makeRequest,
  loadEndpoints,
  endpoints: endpointRegistry
};

// Named exports for tests (e.g. axios-mock-adapter needs the axios instance).
export {
  axiosInstance,
  BASE_URL,
  MAX_RETRIES,
  RETRY_BUDGET_MS,
  isTransientError,
  setUnauthorizedHandler,
  handleUnauthorized,
};

export default api;
