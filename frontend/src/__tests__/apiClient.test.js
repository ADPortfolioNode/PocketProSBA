import MockAdapter from 'axios-mock-adapter';
import apiClient, { axiosInstance } from '../api/apiClient';

// apiClient's default export is a small wrapper object (get/post/put/delete),
// so the mock adapter attaches to the underlying axios instance.
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

  describe('Logging', () => {
    it('should log each request', async () => {
      mock.onGet('/api/health').reply(200, { status: 'ok' });

      await apiClient.get('/api/health');

      expect(console.log).toHaveBeenCalledWith('Making request to:', expect.stringContaining('/api/health'));
    });

    it('should log errors unless quiet', async () => {
      mock.onGet('/api/health').reply(500, { error: 'Server error' });

      await expect(apiClient.get('/api/health')).rejects.toThrow();
      expect(console.error).toHaveBeenCalledWith('API Error:', expect.any(Object));

      console.error.mockClear();
      await expect(apiClient.get('/api/health', {}, { quiet: true })).rejects.toThrow();
      expect(console.error).not.toHaveBeenCalled();
    });
  });

  describe('Base URL configuration', () => {
    it('should use the configured base URL', () => {
      // No REACT_APP_API_URL in tests: same-origin, with localhost mapped to 127.0.0.1.
      const { protocol, port } = window.location;
      const expected = process.env.REACT_APP_API_URL
        ? process.env.REACT_APP_API_URL.replace(/\/api\/?$/, '').replace(/\/+$/, '').replace('://localhost', '://127.0.0.1')
        : `${protocol}//127.0.0.1${port ? `:${port}` : ''}`;
      expect(axiosInstance.defaults.baseURL).toBe(expected);
    });
  });
});
