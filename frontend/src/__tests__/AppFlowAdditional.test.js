import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

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

jest.mock('../components/ModernConciergeChat', () => (props) => {
  const { onSend, messages = [], loading, userName } = props;
  return (
    <div>
      <div>Mocked ModernConciergeChat Component</div>
      <button onClick={() => onSend && onSend('test message')}>Send</button>
      <div>{messages.length} messages</div>
      {loading && <div>Loading...</div>}
      <div>{userName}</div>
    </div>
  );
});

const MainLayout = require('../components/MainLayout').default;

beforeAll(() => {
  // Mock window.alert to avoid not implemented error in tests
  window.alert = jest.fn();
});

describe('Additional  Frontend Application Flow Tests', () => {
  test('Chat tab message sending and response', async () => {
    render(
      <MemoryRouter>
        <MainLayout useConnectionHook={mockUseConnection} />
      </MemoryRouter>
    );

    // Wait for the initial connection health check to complete
    await waitFor(() => {
      expect(screen.getByText(/Mocked ModernConciergeChat Component/i)).toBeInTheDocument();
    });

    // Switch to chat tab if not default
    fireEvent.click(screen.getByTestId('nav-chat'));

    // Check mocked ModernConciergeChat component presence and send button
    expect(screen.getByText(/Mocked ModernConciergeChat Component/i)).toBeInTheDocument();
    const sendButton = screen.getByRole('button', { name: /Send/i });
    expect(sendButton).toBeInTheDocument();

    // Simulate sending a message - mock component handles this internally
    fireEvent.click(sendButton);

    // Ensure the mock child component is still present after interaction
    await waitFor(() => {
      expect(screen.getByText(/Mocked ModernConciergeChat Component/i)).toBeInTheDocument();
    });
  });

  test('RAG tab workflow interface loads and interacts', async () => {
    render(
      <MemoryRouter>
        <MainLayout useConnectionHook={mockUseConnection} />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Mocked ModernConciergeChat Component/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('nav-rag'));

    // Check for presence of RAG workflow elements (adjust selectors)
    expect(screen.getByText(/Upload Document/i)).toBeInTheDocument();

    // Simulate workflow actions as applicable
    // Example: clicking buttons, filling forms, etc.
  });

  test('Document Center upload and management', async () => {
    const { container } = render(
      <MemoryRouter>
        <MainLayout useConnectionHook={mockUseConnection} />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Mocked ModernConciergeChat Component/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('nav-documents'));

    // Check for upload button/input
    expect(screen.getByText(/Upload Document/i)).toBeInTheDocument();
    const uploadInput = container.querySelector('input[type="file"]');
    expect(uploadInput).toBeInTheDocument();

    // Verify initial no-files state is shown
    expect(screen.getByText(/No files uploaded yet/i)).toBeInTheDocument();
  });

  test('SBA Content tab interaction', async () => {
    render(
      <MemoryRouter>
        <MainLayout useConnectionHook={mockUseConnection} />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Mocked ModernConciergeChat Component/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('nav-sba'));

    // Check for SBA content explorer elements
    expect(screen.getByText(/SBA Programs/i)).toBeInTheDocument();

    // Simulate navigation or interaction within SBA content
  });
});
