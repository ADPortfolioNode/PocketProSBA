import { useMemo, useSyncExternalStore } from 'react';
import { getToken, getUser, isTokenExpired, subscribe } from '../utils/authStorage';

/**
 * Live view of the stored session: re-renders on login, logout, a 401 that
 * clears the token, or a change in another tab.
 */
export const useSession = () => {
  const token = useSyncExternalStore(subscribe, getToken, () => null);
  return useMemo(() => ({
    token,
    user: token ? getUser() : null,
    authenticated: !!token && !isTokenExpired(token),
  }), [token]);
};

export default useSession;
