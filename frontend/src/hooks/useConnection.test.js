import { renderHook, act, waitFor } from '@testing-library/react';
import MockAdapter from 'axios-mock-adapter';
import { useConnection } from './useConnection';
import { axiosInstance } from '../api/apiClient';

describe('useConnection', () => {
  let mock;

  beforeAll(() => {
    // Attach to the axios instance; apiClient's default export is a wrapper.
    mock = new MockAdapter(axiosInstance);
  });

  beforeEach(() => {
    jest.spyOn(console, 'log').mockImplementation(() => {});
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    mock.reset();
    jest.restoreAllMocks();
  });

  afterAll(() => {
    mock.restore();
  });

  it('should initialize with default values and start a health check', async () => {
    mock.onGet('/api/info').reply(200, { status: 'operational' });
    const { result } = renderHook(() => useConnection());
    expect(result.current.serverConnected).toBe(false);
    expect(result.current.backendError).toBe(null);
    expect(result.current.connectionInfo).toBe(null);
    // The mount effect kicks off the first check right away
    expect(result.current.isCheckingHealth).toBe(true);
    await waitFor(() => expect(result.current.isCheckingHealth).toBe(false));
  });

  it('should set serverConnected to true on successful connection', async () => {
    mock.onGet('/api/info').reply(200, { status: 'operational' });
    const { result } = renderHook(() => useConnection());

    await waitFor(() => expect(result.current.serverConnected).toBe(true));
    expect(result.current.connectionInfo).toEqual({ status: 'operational' });
    expect(result.current.backendError).toBe(null);
  });

  it('should set serverConnected to false and backendError on failed connection', async () => {
    mock.onGet('/api/info').networkError();
    const { result } = renderHook(() => useConnection());

    await waitFor(() => expect(result.current.backendError).not.toBeNull());
    expect(result.current.serverConnected).toBe(false);
    expect(result.current.connectionInfo).toBe(null);
  });

  it('should perform an API call successfully', async () => {
    const testData = { message: 'Hello' };
    mock.onGet('/api/info').reply(200, { status: 'operational' });
    mock.onPost('/api/chat').reply(200, testData);

    const { result } = renderHook(() => useConnection());

    let response;
    await act(async () => {
      response = await result.current.apiCall('/api/chat', { method: 'POST', body: JSON.stringify({ text: 'hi' }) });
    });

    expect(response).toEqual(testData);
    expect(JSON.parse(mock.history.post[0].data)).toEqual({ text: 'hi' });
  });

  it('should handle API call errors', async () => {
    mock.onGet('/api/info').reply(200, { status: 'operational' });
    mock.onGet('/api/error').reply(500);

    const { result } = renderHook(() => useConnection());

    await act(async () => {
      await expect(result.current.apiCall('/api/error')).rejects.toThrow();
    });
  });

  it('should fetch diagnostics successfully', async () => {
    const diagnosticsData = { cpu: '50%' };
    mock.onGet('/api/info').reply(200, { status: 'operational' });
    mock.onGet('/api/diagnostics').reply(200, diagnosticsData);

    const { result } = renderHook(() => useConnection());

    let diagnostics;
    await act(async () => {
      diagnostics = await result.current.getDiagnostics();
    });

    expect(diagnostics).toEqual(diagnosticsData);
  });

  it('should handle diagnostics fetch error', async () => {
    mock.onGet('/api/info').reply(200, { status: 'operational' });
    mock.onGet('/api/diagnostics').networkError();

    const { result } = renderHook(() => useConnection());

    let diagnostics;
    await act(async () => {
      diagnostics = await result.current.getDiagnostics();
    });

    expect(diagnostics).toEqual({ error: expect.any(String) });
  });

  it('treats a 401 from diagnostics quietly (no redirect, no session wipe)', async () => {
    const { setSession, getToken, clearSession } = require('../utils/authStorage');
    const { setUnauthorizedHandler } = require('../api/apiClient');
    const onUnauthorized = jest.fn();
    setUnauthorizedHandler(onUnauthorized);
    setSession({ token: 'keep-me' });
    mock.onGet('/api/info').reply(200, { status: 'operational' });
    mock.onGet('/api/diagnostics').reply(401, { code: 'token_missing' });

    const { result } = renderHook(() => useConnection());
    let diagnostics;
    await act(async () => {
      diagnostics = await result.current.getDiagnostics();
    });

    expect(diagnostics).toEqual({ unauthorized: true });
    expect(onUnauthorized).not.toHaveBeenCalled();
    expect(getToken()).toBe('keep-me');
    expect(console.error).not.toHaveBeenCalled();
    setUnauthorizedHandler(null);
    clearSession();
  });

  it('reports status checking -> online, and keeps online during background re-checks', async () => {
    mock.onGet('/api/info').reply(200, { status: 'operational' });
    const { result } = renderHook(() => useConnection());
    expect(result.current.status).toBe('checking');
    await waitFor(() => expect(result.current.status).toBe('online'));

    let resolveSlow;
    mock.onGet('/api/info').reply(() => new Promise((r) => { resolveSlow = () => r([200, { status: 'operational' }]); }));
    act(() => { result.current.checkConnection(); });
    await waitFor(() => expect(result.current.isCheckingHealth).toBe(true));
    expect(result.current.status).toBe('online'); // no flip to checking/offline mid-check
    expect(result.current.backendError).toBeNull();
    await act(async () => { resolveSlow(); });
  });

  it('stays "checking" while a cold backend answers 502s, then goes online', async () => {
    mock.onGet('/api/info').replyOnce(502).onGet('/api/info').replyOnce(502).onGet('/api/info').reply(200, { status: 'operational' });
    const { result } = renderHook(() => useConnection());
    expect(result.current.status).toBe('checking');
    await waitFor(() => expect(result.current.status).toBe('online'));
    expect(result.current.backendError).toBeNull();
  });

  it('goes offline with friendly copy only after retries are exhausted', async () => {
    mock.onGet('/api/info').networkError();
    const { result } = renderHook(() => useConnection());
    await waitFor(() => expect(result.current.status).toBe('offline'));
    expect(result.current.backendError).toMatch(/couldn't reach PocketPro/i);
    expect(result.current.backendError).not.toMatch(/Network Error/);
    expect(mock.history.get.filter((r) => r.url === '/api/info').length).toBeGreaterThan(1);
  });

  it('retryConnection returns to the loading state before re-checking', async () => {
    mock.onGet('/api/info').replyOnce(500).onGet('/api/info').reply(200, { status: 'operational' });
    const { result } = renderHook(() => useConnection());
    await waitFor(() => expect(result.current.status).toBe('offline'));
    act(() => { result.current.retryConnection(); });
    expect(result.current.status).toBe('checking');
    await waitFor(() => expect(result.current.status).toBe('online'));
  });

  it('should reset connection by re-checking health', async () => {
    mock.onGet('/api/info').replyOnce(500).onGet('/api/info').reply(200, { status: 'operational' });

    const { result } = renderHook(() => useConnection());

    await waitFor(() => expect(result.current.backendError).not.toBeNull());
    expect(result.current.serverConnected).toBe(false);

    await act(async () => {
      await result.current.resetConnection();
    });

    await waitFor(() => expect(result.current.serverConnected).toBe(true));
  });
});
