import React, { useState } from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ModernConciergeChat from './ModernConciergeChat';

// The chat is controlled: MainLayout owns `messages` and passes `onSend`.
// This harness plays MainLayout's part.
const Harness = ({ reply = 'Hi there', delay = 0 }) => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const onSend = async (text) => {
    setMessages((m) => [...m, { role: 'user', content: text }]);
    setLoading(true);
    await new Promise((r) => setTimeout(r, delay));
    setMessages((m) => [...m, { role: 'assistant', content: reply }]);
    setLoading(false);
  };
  return <ModernConciergeChat onSend={onSend} messages={messages} loading={loading} userName="User" />;
};

describe('ModernConciergeChat', () => {
  test('renders chat interface', () => {
    render(<ModernConciergeChat />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
  });

  test('displays welcome message on load', () => {
    render(<ModernConciergeChat />);
    expect(screen.getByText(/welcome/i)).toBeInTheDocument();
  });

  test('handles user input and sends message', async () => {
    render(<Harness reply="Here is how 7(a) works" />);
    const input = screen.getByRole('textbox');

    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.click(screen.getByRole('button', { name: /send/i }));

    await waitFor(() => {
      expect(screen.getByText('Hello')).toBeInTheDocument();
    });
    expect(await screen.findByText(/Here is how 7\(a\) works/)).toBeInTheDocument();
    await waitFor(() => expect(input).toHaveValue(''));
  });

  test('displays loading state while processing', async () => {
    render(<Harness delay={50} />);
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Test message' } });
    fireEvent.click(screen.getByRole('button', { name: /send/i }));

    expect(await screen.findByLabelText(/thinking/i)).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByLabelText(/thinking/i)).not.toBeInTheDocument());
  });

  test('keeps chat visible and lists conversation links in the Resources tab', () => {
    const messages = [
      {
        role: 'assistant',
        content: 'See [SBA Loans](/browse) for details.',
        sources: [{ title: 'SBA Loans', path: '/api/sba/content/loans' }],
      },
    ];
    render(<ModernConciergeChat messages={messages} />);
    // Chat itself is still present and usable.
    expect(screen.getByRole('textbox')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
    // Links live in the tabbed panel, not only inline.
    expect(screen.getByRole('tab', { name: /^links$/i })).toBeInTheDocument();
    expect(screen.getByText('Links & resources')).toBeInTheDocument();
  });

  test('resources tab links an API source to /browse, not raw JSON', () => {
    const messages = [
      {
        role: 'assistant',
        content: 'See SBA loans.',
        sources: [{ title: 'SBA Loans', path: '/api/sba/content/loans' }],
      },
    ];
    render(<ModernConciergeChat messages={messages} />);
    const link = screen.getByText('SBA Loans');
    expect(link).toHaveAttribute(
      'href',
      '/browse#r=%2Fapi%2Fsba%2Fcontent%2Floans&t=loans',
    );
  });

  test('shows one fixed SBA tip instead of rotating it while typing', () => {
    render(<ModernConciergeChat />);
    expect(
      screen.getByText(/SBA offers resources for business planning/),
    ).toBeInTheDocument();
  });

  test('shows an error when onSend is missing', () => {
    render(<ModernConciergeChat />);
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'x' } });
    fireEvent.click(screen.getByRole('button', { name: /send/i }));
    expect(screen.getByRole('alert')).toHaveTextContent(/not properly configured/i);
  });
});
