import React from 'react';
import '@testing-library/jest-dom';
import { screen, fireEvent } from '@testing-library/react';
import apiClient from '../api/apiClient';
import { renderWithProviders, healthyGet, signInForTests, signOutForTests } from '../test-utils';
import MainLayout from './MainLayout';

jest.mock('../api/apiClient');
jest.mock('./ModernConciergeChat', () => () => <div>Chat view</div>);

const connection = (overrides = {}) => () => ({
  serverConnected: true,
  backendError: null,
  isCheckingHealth: false,
  connectionInfo: {},
  checkConnection: jest.fn(),
  apiCall: jest.fn(),
  getDiagnostics: jest.fn().mockResolvedValue({ status: 'operational' }),
  resetConnection: jest.fn(),
  ...overrides,
});

// Chat, RAG/Tasks and Docs are behind the sign-in guard.
beforeEach(() => signInForTests());
afterEach(() => signOutForTests());

describe('MainLayout', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    apiClient.get.mockImplementation(healthyGet);
  });

  test('renders header, primary nav and footer around the Home view at /', () => {
    renderWithProviders(<MainLayout useConnectionHook={connection()} />, { route: '/' });
    expect(screen.getByRole('banner')).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: /Primary/i })).toBeInTheDocument();
    expect(screen.getByRole('contentinfo')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Funding guidance built for small business/i })).toBeInTheDocument();
  });

  test('unknown routes fall back to the chat view', () => {
    renderWithProviders(<MainLayout useConnectionHook={connection()} />, { route: '/does-not-exist' });
    expect(screen.getByText('Chat view')).toBeInTheDocument();
  });

  test('while the first connection check is pending it shows the loader, never an error', () => {
    renderWithProviders(
      <MainLayout useConnectionHook={connection({ status: 'checking', serverConnected: false })} />,
      { route: '/chat' }
    );
    expect(screen.getByRole('progressbar', { name: /Connecting to PocketPro/i })).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.queryByText(/error/i)).not.toBeInTheDocument();
    expect(screen.queryByText('Chat view')).not.toBeInTheDocument();
  });

  test('a hook without `status` that has no result yet also reads as loading', () => {
    renderWithProviders(
      <MainLayout useConnectionHook={connection({ status: undefined, serverConnected: false, backendError: null })} />,
      { route: '/rag' }
    );
    expect(screen.getByTestId('connection-loading')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  test('Home is static and renders even while the backend is still connecting', () => {
    renderWithProviders(
      <MainLayout useConnectionHook={connection({ status: 'checking', serverConnected: false })} />,
      { route: '/' }
    );
    expect(screen.getByRole('heading', { name: /Funding guidance built for small business/i })).toBeInTheDocument();
    expect(screen.queryByTestId('connection-loading')).not.toBeInTheDocument();
  });

  test('after a real failure it shows a friendly error with Retry (no raw exception text)', () => {
    const retryConnection = jest.fn();
    renderWithProviders(
      <MainLayout
        useConnectionHook={connection({
          status: 'offline',
          serverConnected: false,
          backendError: "We couldn't reach PocketPro. Check your connection and try again.",
          retryConnection,
        })}
      />,
      { route: '/chat' }
    );
    expect(screen.queryByText('Chat view')).not.toBeInTheDocument();
    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent(/can't reach PocketPro/i);
    expect(alert).not.toHaveTextContent(/status code|AxiosError|Backend URL/i);
    fireEvent.click(screen.getByRole('button', { name: /^Retry$/i }));
    expect(retryConnection).toHaveBeenCalled();
  });

});
