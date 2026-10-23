import React from 'react';
import '@testing-library/jest-dom';
import { screen, fireEvent } from '@testing-library/react';
import apiClient from '../../api/apiClient';
import { renderWithProviders, healthyGet, signInForTests, signOutForTests } from '../../test-utils';
import MainLayout from '../MainLayout';

jest.mock('../../api/apiClient');

// Real ModernConciergeChat inside MainLayout (MainLayout.test.js mocks the chat).
const connection = (overrides = {}) => () => ({
  status: 'online',
  serverConnected: true,
  backendError: null,
  isCheckingHealth: false,
  connectionInfo: {},
  checkConnection: jest.fn(),
  retryConnection: jest.fn(),
  apiCall: jest.fn(),
  ...overrides,
});

// Chat, RAG/Tasks and Docs are behind the sign-in guard.
beforeEach(() => signInForTests());
afterEach(() => signOutForTests());

describe('Chat failure handling', () => {
  beforeEach(() => {
    apiClient.get.mockImplementation(healthyGet);
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });
  afterEach(() => console.error.mockRestore());

  test('a failed chat send keeps the draft and offers one friendly "Try again"', async () => {
    const apiCall = jest.fn()
      .mockRejectedValueOnce({ response: { status: 500, data: { error: 'Failed to process message: KeyError' } } })
      .mockResolvedValueOnce({ response: 'Here is how 7(a) works' });
    const { container } = renderWithProviders(
      <MainLayout useConnectionHook={connection({ apiCall })} />,
      { route: '/chat' }
    );
    const input = container.querySelector('textarea');
    fireEvent.change(input, { target: { value: 'Tell me about 7(a)' } });
    fireEvent.click(screen.getByRole('button', { name: /^Send$/i }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/on our side/i);
    expect(alert).not.toHaveTextContent(/KeyError|Failed to process/);
    expect(input).toHaveValue('Tell me about 7(a)');
    // One error only: no extra "Failed to send message" system bubble
    expect(screen.getAllByRole('alert')).toHaveLength(1);
    expect(screen.queryByText(/Failed to send message/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Try again/i }));
    expect(await screen.findByText(/Here is how 7\(a\) works/)).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  test('shows the typing indicator only while a message is in flight', async () => {
    let resolve;
    const apiCall = jest.fn(() => new Promise((r) => { resolve = r; }));
    const { container } = renderWithProviders(
      <MainLayout useConnectionHook={connection({ apiCall })} />,
      { route: '/chat' }
    );
    expect(screen.queryByLabelText(/thinking/i)).not.toBeInTheDocument();
    fireEvent.change(container.querySelector('textarea'), { target: { value: 'Hi' } });
    fireEvent.click(screen.getByRole('button', { name: /^Send$/i }));
    expect(await screen.findByLabelText(/thinking/i)).toBeInTheDocument();
    resolve({ response: 'Hello!' });
    expect(await screen.findByText('Hello!')).toBeInTheDocument();
    expect(screen.queryByLabelText(/thinking/i)).not.toBeInTheDocument();
  });

  test('a prompt card draft from Home pre-fills the chat input', () => {
    const { container } = renderWithProviders(
      <MainLayout useConnectionHook={connection()} />,
      { route: { pathname: '/chat', state: { draft: 'Compare 7(a) and 504 at a glance.' } } }
    );
    expect(container.querySelector('textarea')).toHaveValue('Compare 7(a) and 504 at a glance.');
  });
});
