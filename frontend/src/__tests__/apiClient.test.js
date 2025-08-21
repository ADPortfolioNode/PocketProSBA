import apiClient from '../api/apiClient';
import MockAdapter from 'axios-mock-adapter';

let mock;

beforeEach(() => {
  mock = new MockAdapter(apiClient);
});

afterEach(() => {
  mock.restore();
});

describe('apiClient', () => {
  it('should make a GET request successfully', async () => {
    const data = { message: 'Success' };
    mock.onGet('/test').reply(200, data);

    const response = await apiClient.get('/test');
    expect(response.status).toBe(200);
    expect(response.data).toEqual(data);
  });

  it('should handle a POST request successfully', async () => {
    const requestData = { name: 'test' };
    const responseData = { id: 1, name: 'test' };
    mock.onPost('/create', requestData).reply(201, responseData);

    const response = await apiClient.post('/create', requestData);
    expect(response.status).toBe(201);
    expect(response.data).toEqual(responseData);
  });

  it('should handle API errors', async () => {
    const errorMessage = 'Something went wrong';
    mock.onGet('/error').reply(500, { error: errorMessage });

    await expect(apiClient.get('/error')).rejects.toThrow();
    await apiClient.get('/error').catch(error => {
      expect(error.response.status).toBe(500);
      expect(error.response.data).toEqual({ error: errorMessage });
    });
  });
});