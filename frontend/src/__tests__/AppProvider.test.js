import React from 'react';
import { render, waitFor } from '@testing-library/react';
import { AppProvider, useApp } from '../context/AppProvider';
import apiClient from '../api/apiClient';
import userEvent from '@testing-library/user-event';

jest.mock('../api/apiClient');

const TestComponent = () => {
  const { systemStatus, error, clearError } = useApp();

  return (
    <div>
      <div data-testid="flask-status">{systemStatus.flask.status}</div>
      <div data-testid="chroma-status">{systemStatus.chromadb.status}</div>
      {error && (
        <div>
          <span data-testid="error-message">{error}</span>
          <button onClick={clearError}>Clear</button>
        </div>
      )}
    </div>
  );
};

describe('AppProvider', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches and sets system status on mount', async () => {
    apiClient.get.mockImplementation((url) => {
      if (url === '/api/health') {
        return Promise.resolve({ data: { status: 'ok', message: 'All good' } });
      }
      if (url === '/api/chromadb_health') {
        return Promise.resolve({ data: { status: 'ok', message: 'Chroma OK' } });
      }
      return Promise.reject(new Error('Unknown endpoint'));
    });

    const { getByTestId } = render(
      <AppProvider>
        <TestComponent />
      </AppProvider>
    );

    await waitFor(() => {
      expect(getByTestId('flask-status').textContent).toBe('online');
      expect(getByTestId('chroma-status').textContent).toBe('online');
    });
  });

  it('handles error and clears error state', async () => {
    apiClient.get.mockRejectedValue(new Error('Network error'));

    const { getByTestId, queryByTestId } = render(
      <AppProvider>
        <TestComponent />
      </AppProvider>
    );

    await waitFor(() => {
      expect(getByTestId('error-message').textContent).toBe('Network error');
    });

    userEvent.click(getByTestId('error-message').nextSibling);
    expect(queryByTestId('error-message')).toBeNull();
  });
});
