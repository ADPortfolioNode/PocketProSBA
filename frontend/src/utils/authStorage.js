/**
 * One place for the signed-in session (access token + public user).
 *
 * useAuth writes it on login, apiClient reads it for the Authorization header
 * and clears it on a 401, RequireAuth and the Header read it to decide what
 * to show. Subscribers are told about every change (also across tabs via the
 * browser "storage" event), so the header updates the moment you log in/out.
 */
export const TOKEN_KEY = 'pocketpro_auth_token';
export const USER_KEY = 'pocketpro_auth_user';
export const EXPIRES_KEY = 'pocketpro_auth_expires_at';

const listeners = new Set();

const read = (key) => {
  try {
    return window.localStorage.getItem(key);
  } catch (_) {
    return null;
  }
};

const write = (key, value) => {
  try {
    if (value === null || value === undefined) window.localStorage.removeItem(key);
    else window.localStorage.setItem(key, value);
  } catch (_) {
    /* storage blocked or full: session lasts for this page only */
  }
};

const notify = () => listeners.forEach((fn) => {
  try { fn(); } catch (_) { /* a broken listener must not break auth */ }
});

/** Expiry in ms: the stored expires_at, else the JWT's own exp claim. */
const expiryMs = (token) => {
  const stored = Number(read(EXPIRES_KEY));
  if (stored > 0) return stored * 1000;
  try {
    const part = String(token).split('.')[1];
    if (!part) return null;
    const json = JSON.parse(atob(part.replace(/-/g, '+').replace(/_/g, '/')));
    return typeof json.exp === 'number' ? json.exp * 1000 : null;
  } catch (_) {
    return null;
  }
};

export const getToken = () => read(TOKEN_KEY);

export const getUser = () => {
  const raw = read(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch (_) {
    return null;
  }
};

/** True when the stored token's expiry has passed (unknown expiry = not expired; the server decides). */
export const isTokenExpired = (token = getToken()) => {
  if (!token) return true;
  const ms = expiryMs(token);
  return ms !== null && ms <= Date.now();
};

/** Signed in = a token that hasn't visibly expired. The server still verifies it. */
export const isAuthenticated = () => {
  const token = getToken();
  return !!token && !isTokenExpired(token);
};

export const setSession = ({ token, user, expiresAt } = {}) => {
  if (token) write(TOKEN_KEY, token);
  if (user) write(USER_KEY, JSON.stringify(user));
  write(EXPIRES_KEY, expiresAt ? String(expiresAt) : null);
  notify();
};

export const clearSession = () => {
  write(TOKEN_KEY, null);
  write(USER_KEY, null);
  write(EXPIRES_KEY, null);
  notify();
};

export const subscribe = (fn) => {
  listeners.add(fn);
  return () => listeners.delete(fn);
};

if (typeof window !== 'undefined') {
  window.addEventListener('storage', (e) => {
    if (!e.key || [TOKEN_KEY, USER_KEY, EXPIRES_KEY].includes(e.key)) notify();
  });
}

/** Headers for raw fetch() calls (uploads) that don't go through apiClient. */
export const authHeaders = () => {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
};

/**
 * Only same-app paths are valid return targets after login (no open redirect):
 * must start with a single "/" and not point back at the auth pages.
 */
export const safeReturnPath = (path) => {
  if (typeof path !== 'string' || !path.startsWith('/') || path.startsWith('//') || path.startsWith('/\\')) return '/';
  if (/^\/(login|register|forgot-password)(\/|\?|#|$)/i.test(path)) return '/';
  return path;
};

export const loginPathFor = (returnPath) => {
  const next = safeReturnPath(returnPath);
  return next === '/' ? '/login' : `/login?next=${encodeURIComponent(next)}`;
};
