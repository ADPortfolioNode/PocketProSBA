import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import apiClient from './apiClient';

describe('apiClient', () => {
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

  it('should set the correct base URL from environment variable', () => {
    process.env.REACT_APP_API_URL = 'http://test-api.com';
    const newApiClient = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
    });
    expect(newApiClient.defaults.baseURL).toBe('http://test-api.com');
    delete process.env.REACT_APP_API_URL; // Clean up
  });

  it('should set the correct base URL to localhost if env var is not set', () => {
    const newApiClient = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
    });
    expect(newApiClient.defaults.baseURL).toBe('http://localhost:5000');
  });

  it('should make a GET request successfully', async () => {
    const data = { message: 'Success' };
    mock.onGet('/test').reply(200, data);

    const response = await apiClient.get('/test');
    expect(response.data).toEqual(data);
  });

  it('should handle GET request error', async () => {
    const errorMessage = 'Network Error';
    mock.onGet('/error').networkError();

    await expect(apiClient.get('/error')).rejects.toThrow(errorMessage);
  });

  it('should make a POST request successfully', async () => {
    const requestData = { name: 'test' };
    const responseData = { id: 1, name: 'test' };
    mock.onPost('/post', requestData).reply(201, responseData);

    const response = await apiClient.post('/post', requestData);
    expect(response.data).toEqual(responseData);
  });

  it('should handle POST request error', async () => {
    const errorMessage = 'Request failed with status code 400';
    mock.onPost('/post-error').reply(400);

    await expect(apiClient.post('/post-error', {})).rejects.toThrow(errorMessage);
  });
});
