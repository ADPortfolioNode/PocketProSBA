import { renderHook, act, waitFor } from '@testing-library/react';
import { useConnection } from './useConnection';
import apiClient from '../api/apiClient';
import MockAdapter from 'axios-mock-adapter';

describe('useConnection', () => {
  let mock;

  beforeAll(() => {
    mock = new MockAdapter(apiClient);
  });

  afterEach(() => {
    mock.reset();
  });

  afterAll(() => {
    mock.restore();
  });

  it('should initialize with default values', () => {
    const { result } = renderHook(() => useConnection());
    expect(result.current.serverConnected).toBe(false);
    expect(result.current.backendError).toBe(null);
    expect(result.current.isCheckingHealth).toBe(false);
    expect(result.current.connectionInfo).toBe(null);
  });

  it('should set serverConnected to true on successful connection', async () => {
    mock.onGet('/api/info').reply(200, { status: 'ok' });
    const { result } = renderHook(() => useConnection());

    await waitFor(() => expect(result.current.serverConnected).toBe(true));
    expect(result.current.connectionInfo).toEqual({ status: 'ok' });
    expect(result.current.backendError).toBe(null);
  });

  it('should set serverConnected to false and backendError on failed connection', async () => {
    mock.onGet('/api/info').networkError();
    const { result } = renderHook(() => useConnection());

    await waitFor(() => expect(result.current.serverConnected).toBe(false));
    expect(result.current.backendError).not.toBeNull();
    expect(result.current.connectionInfo).toBe(null);
  });

  it('should perform an API call successfully', async () => {
    const testData = { message: 'Hello' };
    mock.onPost('/api/chat').reply(200, testData);

    const { result } = renderHook(() => useConnection());

    let response;
    await act(async () => {
      response = await result.current.apiCall('/api/chat', { method: 'POST', body: JSON.stringify({ text: 'hi' }) });
    });

    expect(response).toEqual(testData);
  });

  it('should handle API call errors', async () => {
    mock.onGet('/api/error').reply(500);

    const { result } = renderHook(() => useConnection());

    await act(async () => {
      await expect(result.current.apiCall('/api/error')).rejects.toThrow();
    });
  });

  it('should fetch diagnostics successfully', async () => {
    const diagnosticsData = { cpu: '50%' };
    mock.onGet('/api/diagnostics').reply(200, diagnosticsData);

    const { result } = renderHook(() => useConnection());

    let diagnostics;
    await act(async () => {
      diagnostics = await result.current.getDiagnostics();
    });

    expect(diagnostics).toEqual(diagnosticsData);
  });

  it('should handle diagnostics fetch error', async () => {
    mock.onGet('/api/diagnostics').networkError();

    const { result } = renderHook(() => useConnection());

    let diagnostics;
    await act(async () => {
      diagnostics = await result.current.getDiagnostics();
    });

    expect(diagnostics).toEqual({ error: expect.any(String) });
  });

  it('should reset connection by re-checking health', async () => {
    mock.onGet('/api/info').replyOnce(500).onGet('/api/info').reply(200);

    const { result } = renderHook(() => useConnection());

    await waitFor(() => expect(result.current.serverConnected).toBe(false));

    await act(async () => {
      await result.current.resetConnection();
    });

    await waitFor(() => expect(result.current.serverConnected).toBe(true));
  });
});
