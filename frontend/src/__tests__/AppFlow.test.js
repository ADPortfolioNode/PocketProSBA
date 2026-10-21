import React from 'react';
import '@testing-library/jest-dom';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import Login from '../Login';
import apiClient from '../api/apiClient';
import { renderWithProviders, healthyGet, axiosResponse } from '../test-utils';

jest.mock('../api/apiClient');
jest.mock('../components/ModernConciergeChat', () => () => <div>Mocked ModernConciergeChat Component</div>);

const mockUseConnection = () => ({
  serverConnected: true,
  backendError: null,
  isCheckingHealth: false,
  connectionInfo: {},
  checkConnection: jest.fn(),
  apiCall: jest.fn().mockResolvedValue({ response: 'Mock response' }),
  getDiagnostics: jest.fn(),
  resetConnection: jest.fn(),
});

const MainLayout = require('../components/MainLayout').default;

beforeAll(() => {
  // Mock window.alert to avoid not implemented error in tests
  window.alert = jest.fn();
});

beforeEach(() => {
  jest.clearAllMocks();
  apiClient.get.mockImplementation(healthyGet);
});

describe('Frontend Application Flow Tests', () => {
  test('Navigation tabs switch content correctly', async () => {
    // Tabs are routes now (SBANavigation links), active link gets .is-active + aria-current.
    renderWithProviders(<MainLayout useConnectionHook={mockUseConnection} />, { route: '/chat' });

    expect(screen.getByTestId('nav-chat')).toHaveClass('is-active');
    expect(screen.getByTestId('nav-chat')).toHaveAttribute('aria-current', 'page');
    expect(screen.getByText(/Mocked ModernConciergeChat Component/i)).toBeInTheDocument();

    fireEvent.click(screen.getByTestId('nav-rag'));
    await waitFor(() => expect(screen.getByTestId('nav-rag')).toHaveClass('is-active'));
    expect(screen.getByTestId('nav-chat')).not.toHaveClass('is-active');

    fireEvent.click(screen.getByTestId('nav-documents'));
    await waitFor(() => expect(screen.getByTestId('nav-documents')).toHaveClass('is-active'));

    fireEvent.click(screen.getByTestId('nav-orchestrator'));
    await waitFor(() => expect(screen.getByTestId('nav-orchestrator')).toHaveClass('is-active'));
    expect(screen.getByText(/Self-Optimizing Task Orchestrator/i)).toBeInTheDocument();

    fireEvent.click(screen.getByTestId('nav-home'));
    await waitFor(() => expect(screen.getByTestId('nav-home')).toHaveClass('is-active'));

    // Resources and Programs are full page loads (served by nginx), so they are plain anchors.
    expect(screen.getByTestId('nav-browse')).toHaveAttribute('href', '/browse');
    expect(screen.getByTestId('nav-sba')).toHaveAttribute('href', '/sba');
  });

  test('Login page renders and handles form submission', async () => {
    apiClient.post
      .mockRejectedValueOnce({ response: { status: 401, data: { error: 'Invalid credentials' } } })
      .mockResolvedValueOnce(axiosResponse({ user: { email: 'validUser@example.com' }, token: 't' }));

    renderWithProviders(<Login />, { route: '/login' });

    // Check login form elements
    expect(screen.getByLabelText(/Email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Log In/i })).toBeInTheDocument();

    // Invalid login: the backend's message is shown
    fireEvent.change(screen.getByLabelText(/Email address/i), { target: { value: 'invalidUser@example.com' } });
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'wrongPass' } });
    fireEvent.click(screen.getByRole('button', { name: /Log In/i }));

    await waitFor(() => {
      expect(screen.getByText(/Invalid credentials/i)).toBeInTheDocument();
    });

    // Valid login clears the error
    fireEvent.change(screen.getByLabelText(/Email address/i), { target: { value: 'validUser@example.com' } });
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'correctPass' } });
    fireEvent.click(screen.getByRole('button', { name: /Log In/i }));

    await waitFor(() => expect(window.alert).toHaveBeenCalledWith('Login successful!'));
    expect(screen.queryByText(/Invalid credentials/i)).not.toBeInTheDocument();
  });
});
