// Shared test helpers. Not a test file (no .test.js suffix), so Jest won't run it.
import React from 'react';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AppProvider } from './context/AppProvider';
import { clearSession, setSession } from './utils/authStorage';

/**
 * Render a component the way the app does: inside AppProvider and a router.
 * Components that call useApp()/useAuth() or react-router hooks need both.
 *
 *   renderWithProviders(<Login />)
 *   renderWithProviders(<MainLayout />, { route: '/chat' })
 */
export function renderWithProviders(ui, { route = '/', withRouter = true, ...options } = {}) {
  const Wrapper = ({ children }) => (
    <AppProvider>
      {withRouter ? <MemoryRouter initialEntries={[route]}>{children}</MemoryRouter> : children}
    </AppProvider>
  );
  return render(ui, { wrapper: Wrapper, ...options });
}

/**
 * Store a signed-in session so guarded tabs (Chat, RAG/Tasks, Docs) render.
 * Pair with signOutForTests() in afterEach: jsdom localStorage outlives a test.
 */
export const TEST_TOKEN = 'test-access-token';
export function signInForTests(user = { id: 1, email: 'tester@example.com', name: 'Tester' }) {
  setSession({ token: TEST_TOKEN, user, expiresAt: Math.floor(Date.now() / 1000) + 3600 });
}
export const signOutForTests = () => clearSession();

/** Wrapper for renderHook(() => useSomething(), { wrapper: AppWrapper }). */
export const AppWrapper = ({ children }) => <AppProvider>{children}</AppProvider>;

/** Shape an axios-like response the way apiClient resolves. */
export const axiosResponse = (data, status = 200) => ({ data, status, statusText: 'OK', headers: {}, config: {} });

/**
 * Default apiClient.get mock for AppProvider's mount-time health polling.
 * Use with jest.mock('<path>/api/apiClient') in the test file.
 */
export const healthyGet = (url) => {
  if (url === '/api/health') return Promise.resolve(axiosResponse({ status: 'healthy' }));
  if (url === '/api/chromadb_health') return Promise.resolve(axiosResponse({ status: 'ok' }));
  if (url === '/api/info') return Promise.resolve(axiosResponse({ status: 'operational' }));
  return Promise.resolve(axiosResponse({}));
};
