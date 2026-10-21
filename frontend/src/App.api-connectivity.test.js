// App.api-connectivity.test.js
// Verifies the API client's endpoint registry and that /api/health JSON comes back
// through apiClient. The old version fetched a live backend (REACT_APP_BACKEND_URL),
// which can't run in unit CI; the backend side is covered by pytest. Here the HTTP
// layer is mocked at the axios instance.

import MockAdapter from 'axios-mock-adapter';
import apiClient, { axiosInstance } from './api/apiClient';

describe('API Connectivity', () => {
  let mock;
  beforeAll(() => { mock = new MockAdapter(axiosInstance); });
  afterEach(() => mock.reset());
  afterAll(() => mock.restore());

  it('should load the endpoint registry and return valid JSON', async () => {
    const endpoints = await apiClient.loadEndpoints();
    expect(endpoints).toBeDefined();
    expect(typeof endpoints).toBe('object');
    expect(endpoints.endpoints).toBeDefined();
    expect(endpoints.endpoints.api_health).toBe('/api/health');
    expect(endpoints.baseURL).toBe(axiosInstance.defaults.baseURL);
  });

  it('should return valid JSON from /api/health', async () => {
    mock.onGet('/api/health').reply(200, { status: 'healthy', server: { name: 'PocketPro SBA' } }); // shape of backend/routes/api.py /health
    const res = await apiClient.get('/api/health', {}, { quiet: true });
    expect(res.status).toBe(200);
    expect(res.data).toHaveProperty('status', 'healthy');
    expect(res.data).toHaveProperty('server');
  });
});
