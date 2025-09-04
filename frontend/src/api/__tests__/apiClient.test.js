import axios from 'axios';
import apiClient from '../apiClient';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

describe('apiClient', () => {
  beforeEach(() => {
    // Clear all mocks
    jest.clearAllMocks();

    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn(),
      },
      writable: true,
    });
  });

  it('should create axios instance with correct config', () => {
    expect(mockedAxios.create).toHaveBeenCalledWith({
      baseURL: 'http://localhost:5000/api',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  });

  it('should add auth token to request headers when available', async () => {
    const mockToken = 'test-token';
    window.localStorage.getItem.mockReturnValue(mockToken);

    mockedAxios.mockResolvedValue({ data: 'success' });

    await apiClient.get('/test');

    expect(mockedAxios).toHaveBeenCalledWith(
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer test-token',
        }),
      })
    );
  });

  it('should handle 401 errors by clearing token and redirecting', async () => {
    const mockError = {
      response: { status: 401 },
    };

    mockedAxios.mockRejectedValue(mockError);

    try {
      await apiClient.get('/test');
    } catch (error) {
      // Expected to throw
    }

    expect(window.localStorage.removeItem).toHaveBeenCalledWith('authToken');
    // Note: window.location.href would need additional mocking for full test
  });

  it('should handle network errors gracefully', async () => {
    const mockError = {
      message: 'Network Error',
    };

    mockedAxios.mockRejectedValue(mockError);

    await expect(apiClient.get('/test')).rejects.toThrow('Network Error');
  });
});
