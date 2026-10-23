import fs from 'fs';
import path from 'path';
import MockAdapter from 'axios-mock-adapter';
import connectionService from './connectionService';
import { axiosInstance, BASE_URL } from '../api/apiClient';

describe('connectionService', () => {
  let mock;
  let fetchSpy;

  beforeEach(() => {
    mock = new MockAdapter(axiosInstance);
    fetchSpy = jest.fn(() => Promise.reject(new Error('fetch must not be used')));
    global.fetch = fetchSpy;
    jest.spyOn(console, 'warn').mockImplementation(() => {});
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    mock.restore();
    connectionService.stopHealthMonitoring();
    jest.restoreAllMocks();
    delete global.fetch;
  });

  it('has no hard-coded loopback backend URLs', () => {
    const src = fs.readFileSync(path.join(__dirname, 'connectionService.js'), 'utf8');
    expect(src).not.toMatch(/127\.0\.0\.1:5000|localhost:5000/);
  });

  it('probes /api/health through apiClient (REACT_APP_API_URL base)', async () => {
    mock.onGet('/api/health').reply((config) => [200, { status: 'healthy', base: config.baseURL }]);

    const status = await connectionService.checkConnection();

    expect(status.connected).toBe(true);
    expect(status.info.base).toBe(BASE_URL);
    expect(mock.history.get).toHaveLength(1);
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it('falls back to /api/info when /api/health fails', async () => {
    mock.onGet('/api/health').reply(500);
    mock.onGet('/api/info').reply(200, { status: 'operational' });

    const status = await connectionService.checkConnection();

    expect(status).toMatchObject({ connected: true, info: { status: 'operational' } });
  });

  it('reports disconnected when both probes fail', async () => {
    mock.onGet('/api/health').reply(404);
    mock.onGet('/api/info').reply(404);

    const status = await connectionService.checkConnection();

    expect(status.connected).toBe(false);
  });

  it('getDiagnostics treats a 401 quietly', async () => {
    mock.onGet('/api/diagnostics').reply(401, { code: 'token_missing' });

    await expect(connectionService.getDiagnostics()).resolves.toEqual({ unauthorized: true });
    expect(console.error).not.toHaveBeenCalled();
  });
});
