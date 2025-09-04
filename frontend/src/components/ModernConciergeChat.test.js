import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ModernConciergeChat from './ModernConciergeChat';

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
    render(<ModernConciergeChat />);
    const input = screen.getByRole('textbox');
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText('Hello')).toBeInTheDocument();
    });
  });

  test('displays loading state while processing', async () => {
    render(<ModernConciergeChat />);
    const input = screen.getByRole('textbox');
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);

    expect(screen.getByText(/thinking/i)).toBeInTheDocument();
  });
});
