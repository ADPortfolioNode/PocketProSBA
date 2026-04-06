import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AppProvider } from '../context/AppProvider';
import Login from '../Login';

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

describe('Frontend Application Flow Tests', () => {
  test('Navigation tabs switch content correctly', async () => {
    render(
      <MemoryRouter>
        <MainLayout useConnectionHook={mockUseConnection} />
      </MemoryRouter>
    );

    // Check initial tab is chat
    const chatTabs = screen.getAllByText(/Chat/i);
    expect(chatTabs[0]).toHaveClass('active');
    expect(chatTabs[0]).toBeInTheDocument();

    // Click Browse Resources tab
    fireEvent.click(screen.getByTestId('nav-browse'));
    await waitFor(() => {
      expect(screen.getByTestId('nav-browse')).toHaveClass('active');
    });

    // Click RAG tab
    fireEvent.click(screen.getByTestId('nav-rag'));
    await waitFor(() => {
      expect(screen.getByTestId('nav-rag')).toHaveClass('active');
    });

    // Click Document Center tab
    fireEvent.click(screen.getByTestId('nav-documents'));
    await waitFor(() => {
      expect(screen.getByTestId('nav-documents')).toHaveClass('active');
    });

    // Click SBA Content tab
    fireEvent.click(screen.getByText(/SBA Content/i));
    await waitFor(() => {
      expect(screen.getByText(/SBA Content/i)).toHaveClass('active');
    });
  });

  test('Login page renders and handles form submission', async () => {
    render(
      <AppProvider>
        <MemoryRouter>
          <Login />
        </MemoryRouter>
      </AppProvider>
    );

    // Check login form elements
    expect(screen.getByLabelText(/Email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Log In/i })).toBeInTheDocument();

    // Simulate invalid login submission
    fireEvent.change(screen.getByLabelText(/Email address/i), { target: { value: 'invalidUser' } });
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'wrongPass' } });
    fireEvent.click(screen.getByRole('button', { name: /Log In/i }));

    // Expect error message or validation (adjust based on actual implementation)
    await waitFor(() => {
      expect(screen.getByText(/Invalid credentials/i)).toBeInTheDocument();
    });

    // Simulate valid login submission (adjust credentials as needed)
    fireEvent.change(screen.getByLabelText(/Email address/i), { target: { value: 'validUser' } });
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'correctPass' } });
    fireEvent.click(screen.getByRole('button', { name: /Log In/i }));

    // Expect redirect or success message (adjust based on actual implementation)
    await waitFor(() => {
      expect(screen.queryByText(/Invalid credentials/i)).not.toBeInTheDocument();
    });
  });
});
