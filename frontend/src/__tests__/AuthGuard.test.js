import React from 'react';
import '@testing-library/jest-dom';
import { act, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route, useLocation } from 'react-router-dom';
import apiClient, { setUnauthorizedHandler } from '../api/apiClient';
import Login from '../Login';
import { UnauthorizedRedirect } from '../App';
import { renderWithProviders, healthyGet, axiosResponse, signInForTests, signOutForTests } from '../test-utils';
import { getToken, setSession } from '../utils/authStorage';

jest.mock('../api/apiClient');
jest.mock('../components/ModernConciergeChat', () => () => <div>Chat screen</div>);

const MainLayout = require('../components/MainLayout').default;

const mockUseConnection = () => ({
  status: 'online',
  serverConnected: true,
  backendError: null,
  isCheckingHealth: false,
  connectionInfo: {},
  checkConnection: jest.fn(),
  apiCall: jest.fn().mockResolvedValue({ response: 'ok' }),
});

function LocationProbe() {
  const loc = useLocation();
  return <div data-testid="location">{`${loc.pathname}${loc.search}`}</div>;
}

const renderApp = (route) =>
  renderWithProviders(
    <MemoryRouter initialEntries={[route]}>
      <UnauthorizedRedirect />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/*" element={<MainLayout useConnectionHook={mockUseConnection} />} />
      </Routes>
      <LocationProbe />
    </MemoryRouter>,
    { withRouter: false }
  );

beforeEach(() => {
  apiClient.get.mockImplementation(healthyGet);
  window.alert = jest.fn();
  jest.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
  signOutForTests();
  console.error.mockRestore();
});

describe('route guard', () => {
  test.each([
    ['/chat', '/chat'],
    ['/rag', '/rag'],
    ['/documents', '/documents'],
    ['/orchestrator', '/orchestrator'],
  ])('signed-out visit to %s goes to /login with the return path', async (route, back) => {
    renderApp(route);
    expect(await screen.findByRole('button', { name: /Log In/i })).toBeInTheDocument();
    expect(screen.getByTestId('location')).toHaveTextContent(`/login?next=${encodeURIComponent(back)}`);
    expect(screen.getByText(/Please log in to continue/i)).toBeInTheDocument();
  });

  test('Home stays public', () => {
    renderApp('/');
    expect(screen.getByTestId('location')).toHaveTextContent(/^\/$/);
    expect(screen.queryByRole('button', { name: /^Log In$/i })).not.toBeInTheDocument();
  });

  test('a signed-in user sees the protected tab', () => {
    signInForTests();
    renderApp('/chat');
    expect(screen.getByText('Chat screen')).toBeInTheDocument();
    expect(screen.getByTestId('location')).toHaveTextContent('/chat');
  });

  test('an expired stored session is treated as signed out', () => {
    setSession({ token: 'old', expiresAt: Math.floor(Date.now() / 1000) - 5 });
    renderApp('/documents');
    expect(screen.getByTestId('location')).toHaveTextContent('/login?next=%2Fdocuments');
  });

  test('logging in returns to the page that needed sign-in', async () => {
    apiClient.post.mockResolvedValueOnce(axiosResponse({
      token: 'new.jwt.token', token_type: 'Bearer', expires_in: 3600,
      expires_at: Math.floor(Date.now() / 1000) + 3600, user: { email: 'a@b.co' },
    }));
    renderApp('/rag');
    await screen.findByRole('button', { name: /Log In/i });

    fireEvent.change(screen.getByLabelText(/Email address/i), { target: { value: 'a@b.co' } });
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /Log In/i }));

    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent(/^\/rag$/));
    expect(getToken()).toBe('new.jwt.token');
  });

  test('a hostile ?next= falls back to Home', async () => {
    apiClient.post.mockResolvedValueOnce(axiosResponse({ token: 't', user: { email: 'a@b.co' } }));
    renderApp('/login?next=%2F%2Fevil.example');
    fireEvent.change(screen.getByLabelText(/Email address/i), { target: { value: 'a@b.co' } });
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /Log In/i }));
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent(/^\/$/));
  });
});

describe('header sign-in state', () => {
  test('signed out: shows Log in', () => {
    renderApp('/');
    expect(screen.getByRole('link', { name: /^Log in$/i })).toHaveAttribute('href', '/login');
    expect(screen.queryByRole('button', { name: /Log out/i })).not.toBeInTheDocument();
  });

  test('signed in: shows the user and Log out, which clears the session', async () => {
    signInForTests({ email: 'tester@example.com', name: 'Tester' });
    renderApp('/chat');
    expect(screen.getByText('Tester')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Log out/i }));

    expect(getToken()).toBeNull();
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent(/^\/$/));
    expect(screen.getByRole('link', { name: /^Log in$/i })).toBeInTheDocument();
  });
});

describe('401 redirect bridge', () => {
  test('registers a router-aware handler that navigates to the login path', async () => {
    signInForTests();
    renderApp('/chat');
    const handler = setUnauthorizedHandler.mock.calls.map((c) => c[0]).filter((fn) => typeof fn === 'function').pop();
    expect(handler).toBeInstanceOf(Function);

    signOutForTests(); // what apiClient does before calling the handler
    act(() => handler('/login?next=%2Fchat'));

    expect(await screen.findByRole('button', { name: /Log In/i })).toBeInTheDocument();
    expect(screen.getByTestId('location')).toHaveTextContent('/login?next=%2Fchat');
  });
});
