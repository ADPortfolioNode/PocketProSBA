import React from 'react';
import '@testing-library/jest-dom';
import { screen, fireEvent } from '@testing-library/react';
import apiClient from '../api/apiClient';
import { renderWithProviders, healthyGet } from '../test-utils';
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

  test('when the backend is unreachable it offers a retry that re-checks the connection', () => {
    const checkConnection = jest.fn();
    renderWithProviders(
      <MainLayout useConnectionHook={connection({ serverConnected: false, backendError: 'Network Error', checkConnection })} />,
      { route: '/chat' }
    );
    expect(screen.queryByText('Chat view')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Retry Connection/i }));
    expect(checkConnection).toHaveBeenCalled();
  });
});
