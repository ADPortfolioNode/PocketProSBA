import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import apiClient from '../api/apiClient';

describe('apiClient', () => {
  let mock;

  beforeEach(() => {
    mock = new MockAdapter(apiClient);
  });

  afterEach(() => {
    mock.restore();
  });

  describe('GET requests', () => {
    it('should make a successful GET request', async () => {
      const mockData = { message: 'Success' };
      mock.onGet('/api/health').reply(200, mockData);

      const response = await apiClient.get('/api/health');
      expect(response.data).toEqual(mockData);
    });

    it('should handle GET request errors', async () => {
      mock.onGet('/api/health').reply(500, { error: 'Server error' });

      await expect(apiClient.get('/api/health')).rejects.toThrow();
    });
  });

  describe('POST requests', () => {
    it('should make a successful POST request', async () => {
      const mockData = { id: 1, message: 'Created' };
      const postData = { name: 'Test' };
      mock.onPost('/api/decompose', postData).reply(200, mockData);

      const response = await apiClient.post('/api/decompose', postData);
      expect(response.data).toEqual(mockData);
    });

    it('should handle POST request errors', async () => {
      const postData = { name: 'Test' };
      mock.onPost('/api/decompose', postData).reply(400, { error: 'Bad request' });

      await expect(apiClient.post('/api/decompose', postData)).rejects.toThrow();
    });
  });

  describe('Interceptors', () => {
    it('should add request interceptor logging', async () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation(() => {});
      mock.onGet('/api/health').reply(200, { status: 'ok' });

      await apiClient.get('/api/health');

      expect(consoleSpy).toHaveBeenCalledWith('Making request to:', expect.stringContaining('/api/health'));
      consoleSpy.mockRestore();
    });

    it('should handle response errors globally', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      mock.onGet('/api/health').reply(500, { error: 'Server error' });

      await expect(apiClient.get('/api/health')).rejects.toThrow();

      expect(consoleSpy).toHaveBeenCalledWith('API Error:', expect.any(Object));
      consoleSpy.mockRestore();
    });
  });

  describe('Base URL configuration', () => {
    it('should use the configured base URL', () => {
      expect(apiClient.defaults.baseURL).toBe(process.env.REACT_APP_API_URL || 'http://localhost:5000');
    });
  });
});
