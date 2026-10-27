import { useEffect, useMemo, useRef, useSyncExternalStore } from 'react';
import apiClient from '../api/apiClient';
import { clearSession, getRefreshToken, getToken, getUser, isTokenExpired, setSession, subscribe } from '../utils/authStorage';

/**
 * Live view of the stored session: re-renders on login, logout, a 401 that
 * clears the token, or a change in another tab.
 *
 * Remember me: an expired access token with a stored refresh token still
 * counts as authenticated — the restore below silently swaps the refresh
 * token for a fresh access token, so returning after days (or after the
 * 1-hour access token expired) does not bounce the user to /login. If the
 * refresh token is rejected (password changed, account disabled, 30 days
 * passed), the session is cleared and the route guard sends them to login.
 */
export const useSession = () => {
  const token = useSyncExternalStore(subscribe, getToken, () => null);
  const restoreTried = useRef(false);
  useEffect(() => {
    if (!token || !isTokenExpired(token) || !getRefreshToken() || restoreTried.current) return;
    restoreTried.current = true;
    apiClient.post('/api/auth/refresh-token', { refresh_token: getRefreshToken() }, { skipAuthRedirect: true })
      .then((res) => {
        const data = res.data || {};
        if (data.token) setSession({ token: data.token, user: data.user, expiresAt: data.expires_at, refreshToken: data.refresh_token });
        else clearSession();
      })
      .catch(() => clearSession());
  }, [token]);
  return useMemo(() => ({
    token,
    user: token ? getUser() : null,
    authenticated: !!token && (!isTokenExpired(token) || !!getRefreshToken()),
  }), [token]);
};

export default useSession;
