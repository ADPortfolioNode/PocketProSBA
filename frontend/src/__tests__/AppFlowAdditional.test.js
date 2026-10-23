import React from 'react';
import '@testing-library/jest-dom';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import apiClient from '../api/apiClient';
import { renderWithProviders, healthyGet, signInForTests, signOutForTests } from '../test-utils';

jest.mock('../api/apiClient');

// CRA's Jest config sets resetMocks, so implementations are (re)applied in beforeEach.
const mockApiCall = jest.fn();
const mockUseConnection = () => ({
  serverConnected: true,
  backendError: null,
  isCheckingHealth: false,
  connectionInfo: {},
  checkConnection: jest.fn(),
  apiCall: mockApiCall,
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

// Chat, RAG/Tasks and Docs are behind the sign-in guard.
beforeEach(() => signInForTests());
afterEach(() => signOutForTests());

beforeAll(() => {
  // Mock window.alert to avoid not implemented error in tests
  window.alert = jest.fn();
});

beforeEach(() => {
  jest.clearAllMocks();
  apiClient.get.mockImplementation(healthyGet);
  mockApiCall.mockResolvedValue({ response: 'Mock response' });
});

const renderAt = (route) => renderWithProviders(<MainLayout useConnectionHook={mockUseConnection} />, { route });

describe('Additional  Frontend Application Flow Tests', () => {
  test('Chat tab message sending and response', async () => {
    renderAt('/chat');

    expect(screen.getByText(/Mocked ModernConciergeChat Component/i)).toBeInTheDocument();
    expect(screen.getByText('0 messages')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Send/i }));

    // User message + assistant reply are appended by MainLayout.handleChatSend
    await waitFor(() => expect(screen.getByText('2 messages')).toBeInTheDocument());
    expect(mockApiCall).toHaveBeenCalledWith('/api/chat', expect.objectContaining({ method: 'POST' }));
  });

  test('RAG tab workflow interface loads and interacts', async () => {
    renderAt('/chat');
    fireEvent.click(screen.getByTestId('nav-rag'));

    expect(await screen.findByText(/Upload Document/i)).toBeInTheDocument();
    fireEvent.click(screen.getByText(/Start Task Without Upload/i));
    expect(screen.getByText(/Describe your task/i)).toBeInTheDocument();
  });

  test('Document Center upload and management', async () => {
    const { container } = renderAt('/chat');
    fireEvent.click(screen.getByTestId('nav-documents'));

    // Check for upload button/input
    expect(await screen.findByText(/Upload Document/i)).toBeInTheDocument();
    const uploadInput = container.querySelector('input[type="file"]');
    expect(uploadInput).toBeInTheDocument();

    // Verify initial no-files state is shown
    // The Docs tab loads GET /api/documents/list itself (the mock returns no files).
    expect(await screen.findByText(/No files uploaded yet/i)).toBeInTheDocument();
    expect(apiClient.get).toHaveBeenCalledWith('/api/documents/list', {}, { quiet: true });
  });

  test('SBA Content route renders the programs view', async () => {
    // /sba is a full page load from the nav (programs.html via nginx); the SPA
    // route still renders SBAContent when reached directly.
    renderAt('/sba');
    await waitFor(() => expect(apiClient.get).toHaveBeenCalledWith('/api/sba/resources', expect.anything(), { quiet: true }));
    expect(screen.getByTestId('nav-sba')).toHaveClass('is-active');
  });
});
