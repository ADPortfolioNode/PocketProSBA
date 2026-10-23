import {
  authHeaders,
  clearSession,
  getToken,
  getUser,
  isAuthenticated,
  loginPathFor,
  safeReturnPath,
  setSession,
  subscribe,
} from './authStorage';

const jwtWithExp = (exp) => `h.${btoa(JSON.stringify({ exp })).replace(/=+$/, '')}.s`;

describe('authStorage', () => {
  afterEach(() => clearSession());

  it('stores and clears the session and notifies subscribers', () => {
    const fn = jest.fn();
    const off = subscribe(fn);
    setSession({ token: 't1', user: { email: 'a@b.co' }, expiresAt: Math.floor(Date.now() / 1000) + 60 });
    expect(getToken()).toBe('t1');
    expect(getUser()).toEqual({ email: 'a@b.co' });
    expect(isAuthenticated()).toBe(true);
    expect(authHeaders()).toEqual({ Authorization: 'Bearer t1' });
    clearSession();
    expect(getToken()).toBeNull();
    expect(isAuthenticated()).toBe(false);
    expect(authHeaders()).toEqual({});
    expect(fn).toHaveBeenCalledTimes(2);
    off();
  });

  it('treats an expired session as signed out', () => {
    setSession({ token: 't', expiresAt: Math.floor(Date.now() / 1000) - 10 });
    expect(isAuthenticated()).toBe(false);
  });

  it('falls back to the JWT exp claim when no expiry was stored', () => {
    setSession({ token: jwtWithExp(Math.floor(Date.now() / 1000) - 10) });
    expect(isAuthenticated()).toBe(false);
    setSession({ token: jwtWithExp(Math.floor(Date.now() / 1000) + 600) });
    expect(isAuthenticated()).toBe(true);
  });

  it('only allows same-app return paths (no open redirect)', () => {
    expect(safeReturnPath('/chat?x=1')).toBe('/chat?x=1');
    expect(safeReturnPath('//evil.example')).toBe('/');
    expect(safeReturnPath('https://evil.example')).toBe('/');
    expect(safeReturnPath('/\\evil.example')).toBe('/');
    expect(safeReturnPath('/login?next=/chat')).toBe('/');
    expect(safeReturnPath(undefined)).toBe('/');
    expect(loginPathFor('/rag')).toBe('/login?next=%2Frag');
    expect(loginPathFor('/')).toBe('/login');
  });
});
