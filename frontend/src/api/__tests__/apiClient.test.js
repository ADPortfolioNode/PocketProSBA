import MockAdapter from 'axios-mock-adapter';
import apiClient, { axiosInstance, MAX_RETRIES } from '../apiClient';

// Earlier versions of this file asserted an auth-token request interceptor and a
// 401 -> clear-token/redirect handler, plus a '/api' baseURL with a 10s timeout.
// apiClient has none of those today (useAuth stores the token but nothing sends
// it), so those assertions were replaced with the client's actual contract.
describe('apiClient', () => {
  let mock;

  beforeEach(() => {
    mock = new MockAdapter(axiosInstance);
    jest.spyOn(console, 'log').mockImplementation(() => {});
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    mock.restore();
    jest.restoreAllMocks();
  });

  it('should create axios instance with correct config', () => {
    expect(axiosInstance.defaults.timeout).toBe(60000);
    expect(axiosInstance.defaults.headers['Content-Type']).toBe('application/json');
    expect(typeof axiosInstance.defaults.baseURL).toBe('string');
  });

  it('should pass request config (params, headers) through to axios', async () => {
    mock.onGet('/test').reply((config) => [200, { params: config.params, auth: config.headers.Authorization }]);

    const res = await apiClient.get('/test', { params: { q: 'loans' }, headers: { Authorization: 'Bearer t' } });

    expect(res.data).toEqual({ params: { q: 'loans' }, auth: 'Bearer t' });
  });

  it('should retry refused connections before giving up', async () => {
    // Skip the 1s back-off between attempts.
    jest.spyOn(global, 'setTimeout').mockImplementation((fn) => { fn(); return 0; });
    const refused = () => Object.assign(new Error('connect ECONNREFUSED'), { code: 'ECONNREFUSED' });
    let calls = 0;
    mock.onGet('/test').reply(() => {
      calls += 1;
      return Promise.reject(refused());
    });

    await expect(apiClient.get('/test', {}, { quiet: true })).rejects.toThrow('ECONNREFUSED');
    expect(calls).toBe(MAX_RETRIES + 1);
  });

  it('should handle network errors gracefully', async () => {
    mock.onGet('/test').networkError();

    await expect(apiClient.get('/test')).rejects.toThrow('Network Error');
  });
});
