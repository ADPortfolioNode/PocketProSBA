// App.api-connectivity.test.js
// Minimal Jest test to verify backend API connectivity and JSON responses

import { loadEndpoints } from './apiClient';

describe('API Connectivity', () => {
  it('should load the endpoint registry and return valid JSON', async () => {
    const endpoints = await loadEndpoints();
    expect(endpoints).toBeDefined();
    expect(typeof endpoints).toBe('object');
    expect(endpoints.endpoints).toBeDefined();
    expect(endpoints.endpoints.api_health).toBe('/api/health');
  });

  it('should return valid JSON from /api/health', async () => {
    const res = await fetch(process.env.REACT_APP_BACKEND_URL + '/api/health');
    expect(res.ok).toBe(true);
    const json = await res.json();
    expect(json).toHaveProperty('status', 'healthy');
    expect(json).toHaveProperty('service');
    expect(json).toHaveProperty('version');
  });
});
