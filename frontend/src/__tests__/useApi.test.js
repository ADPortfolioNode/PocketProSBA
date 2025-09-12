import { renderHook, act, waitFor } from '@testing-library/react';
import { useApi, useSBAContent } from '../hooks/useApi';
import apiClient from '../api/apiClient';
import { AppProvider } from '../context/AppProvider';

jest.mock('../api/apiClient');

const wrapper = ({ children }) => (
  <AppProvider>{children}</AppProvider>
);

describe('useApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('handles successful GET request', async () => {
    const mockData = { message: 'Success' };
    apiClient.get.mockResolvedValue({ data: mockData });

    const { result } = renderHook(() => useApi(), { wrapper });

    let response;
    await act(async () => {
      response = await result.current.get('/api/health');
    });

    expect(response).toEqual(mockData);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe(null);
  });

  it('handles GET request error', async () => {
    const errorMessage = 'Network error';
    apiClient.get.mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useApi(), { wrapper });

    await act(async () => {
      try {
        await result.current.get('/api/health');
      } catch (error) {
        // Expected error
      }
    });

    expect(result.current.error).toBe(errorMessage);
    expect(result.current.loading).toBe(false);
  });

  it('handles successful POST request', async () => {
    const mockData = { id: 1 };
    const postData = { name: 'Test' };
    apiClient.post.mockResolvedValue({ data: mockData });

    const { result } = renderHook(() => useApi(), { wrapper });

    let response;
    await act(async () => {
      response = await result.current.post('/api/decompose', postData);
    });

    expect(response).toEqual(mockData);
  });

  it('clears error on clearError call', async () => {
    apiClient.get.mockRejectedValue(new Error('Error'));

    const { result } = renderHook(() => useApi(), { wrapper });

    await act(async () => {
      try {
        await result.current.get('/api/health');
      } catch (error) {
        // Expected error
      }
    });

    expect(result.current.error).toBe('Error');

    act(() => {
      result.current.clearError();
    });

    expect(result.current.error).toBe(null);
  });
});

describe('useSBAContent', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('searches content successfully', async () => {
    const mockData = {
      items: [{ id: 1, title: 'Test Article' }],
      totalPages: 1,
      currentPage: 1
    };
    apiClient.get.mockResolvedValue({ data: mockData });

    const { result } = renderHook(() => useSBAContent(), { wrapper });

    let response;
    await act(async () => {
      response = await result.current.searchContent('articles', 'test', 1);
    });

    expect(response).toEqual(mockData);
    expect(apiClient.get).toHaveBeenCalledWith('/api/sba/content/articles', {
      params: { query: 'test', page: 1 }
    });
  });

  it('gets content details successfully', async () => {
    const mockData = { id: 1, title: 'Test Article', body: 'Content' };
    apiClient.get.mockResolvedValue({ data: mockData });

    const { result } = renderHook(() => useSBAContent(), { wrapper });

    let response;
    await act(async () => {
      response = await result.current.getContentDetails('articles', 1);
    });

    expect(response).toEqual(mockData);
    expect(apiClient.get).toHaveBeenCalledWith('/api/sba/content/articles/1');
  });

  it('gets node details successfully', async () => {
    const mockData = { id: 1, title: 'Test Node' };
    apiClient.get.mockResolvedValue({ data: mockData });

    const { result } = renderHook(() => useSBAContent(), { wrapper });

    let response;
    await act(async () => {
      response = await result.current.getNodeDetails(1);
    });

    expect(response).toEqual(mockData);
    expect(apiClient.get).toHaveBeenCalledWith('/api/sba/content/node/1');
  });
});
