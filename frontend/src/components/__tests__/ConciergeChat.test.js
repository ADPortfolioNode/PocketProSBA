import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ConciergeChat from '../ConciergeChat';

jest.useFakeTimers();

describe('ConciergeChat Component', () => {
  const onSendMock = jest.fn();

  beforeEach(() => {
    onSendMock.mockClear();
  });

  test('renders without errors with empty messages', () => {
    render(<ConciergeChat onSend={onSendMock} messages={[]} loading={false} />);
    expect(screen.getByText(/Start the conversation below!/i)).toBeInTheDocument();
  });

  test('renders messages correctly', () => {
    const messages = [
      { role: 'user', content: 'Hello' },
      { role: 'assistant', content: 'Hi there!' },
    ];
    render(<ConciergeChat onSend={onSendMock} messages={messages} loading={false} />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi there!')).toBeInTheDocument();
  });

  test('input and send button work correctly', () => {
    render(<ConciergeChat onSend={onSendMock} messages={[]} loading={false} />);
    const input = screen.getByPlaceholderText(/Type your message.../i);
    const button = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'Test message' } });
    expect(input.value).toBe('Test message');

    fireEvent.click(button);
    expect(onSendMock).toHaveBeenCalledWith('Test message');
    expect(input.value).toBe('');
  });

  test('SBA tips rotate every 5 seconds', async () => {
    render(<ConciergeChat onSend={onSendMock} messages={[]} loading={false} />);
    const firstTip = screen.getByText(/SBA offers resources for business planning/i);
    expect(firstTip).toBeInTheDocument();

    jest.advanceTimersByTime(5000);
    await waitFor(() => {
      expect(screen.getByText(/Did you know\? SBA offers disaster assistance loans/i)).toBeInTheDocument();
    });

    jest.advanceTimersByTime(5000);
    await waitFor(() => {
      expect(screen.getByText(/SBA's 7\(a\) loan program is their primary program/i)).toBeInTheDocument();
    });
  });
});
