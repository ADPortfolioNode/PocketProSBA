import MockAdapter from 'axios-mock-adapter';
import apiClient, { axiosInstance, setUnauthorizedHandler } from '../apiClient';
import { clearSession, getToken, setSession } from '../../utils/authStorage';

// apiClient sends the stored access token and turns a 401 into a sign-out +
// redirect to /login?next=<where the user was>.
describe('apiClient authentication', () => {
  let mock;
  let redirect;

  beforeEach(() => {
    mock = new MockAdapter(axiosInstance);
    redirect = jest.fn();
    setUnauthorizedHandler(redirect);
    jest.spyOn(console, 'log').mockImplementation(() => {});
    jest.spyOn(console, 'error').mockImplementation(() => {});
    window.history.pushState({}, '', '/');
  });

  afterEach(() => {
    mock.restore();
    setUnauthorizedHandler(null);
    clearSession();
    jest.restoreAllMocks();
  });

  it('attaches Authorization: Bearer <token> from the stored session', async () => {
    setSession({ token: 'abc.def.ghi', user: { email: 'a@b.co' } });
    mock.onGet('/api/documents/list').reply((config) => [200, { auth: config.headers.Authorization }]);

    const res = await apiClient.get('/api/documents/list');

    expect(res.data.auth).toBe('Bearer abc.def.ghi');
  });

  it('sends no Authorization header when signed out', async () => {
    mock.onGet('/api/health').reply((config) => [200, { auth: config.headers.Authorization || null }]);
    const res = await apiClient.get('/api/health');
    expect(res.data.auth).toBeNull();
  });

  it('keeps an Authorization header the caller set explicitly', async () => {
    setSession({ token: 'stored' });
    mock.onGet('/x').reply((config) => [200, { auth: config.headers.Authorization }]);
    const res = await apiClient.get('/x', { headers: { Authorization: 'Bearer explicit' } });
    expect(res.data.auth).toBe('Bearer explicit');
  });

  it('on 401 clears the token and redirects to /login with the return path', async () => {
    setSession({ token: 'expired-token' });
    window.history.pushState({}, '', '/chat?topic=loans');
    mock.onPost('/api/chat').reply(401, { error: 'Your session has expired. Please log in again.', code: 'token_expired' });

    await expect(apiClient.post('/api/chat', { message: 'hi' }, {}, { quiet: true })).rejects.toMatchObject({
      response: { status: 401 },
    });

    expect(getToken()).toBeNull();
    expect(redirect).toHaveBeenCalledWith(`/login?next=${encodeURIComponent('/chat?topic=loans')}`);
    // 401 is not a transient error: exactly one request, no retries.
    expect(mock.history.post).toHaveLength(1);
  });

  it('does not redirect on a wrong-password 401 from the login endpoint', async () => {
    setSession({ token: 'keep-me' });
    window.history.pushState({}, '', '/login');
    mock.onPost('/api/login').reply(401, { error: 'Invalid email or password' });

    await expect(apiClient.post('/api/login', {}, {}, { quiet: true })).rejects.toBeTruthy();

    expect(redirect).not.toHaveBeenCalled();
    expect(getToken()).toBe('keep-me');
  });

  it('does not redirect for other status codes', async () => {
    setSession({ token: 'keep-me' });
    mock.onGet('/api/documents/list').reply(403, { error: 'nope' });
    await expect(apiClient.get('/api/documents/list', {}, { quiet: true })).rejects.toBeTruthy();
    expect(redirect).not.toHaveBeenCalled();
    expect(getToken()).toBe('keep-me');
  });
});
