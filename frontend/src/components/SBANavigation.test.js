import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import SBANavigation from './SBANavigation';

describe('SBANavigation', () => {
  const mockOnTabChange = jest.fn();

  test('renders navigation menu', () => {
    render(
      <SBANavigation
        activeTab="chat"
        onTabChange={mockOnTabChange}
        serverConnected={true}
        apiUrl="http://localhost"
      />
    );
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getByText(/Chat/i)).toBeInTheDocument();
  });

  test('displays navigation links', () => {
    render(
      <SBANavigation
        activeTab="chat"
        onTabChange={mockOnTabChange}
        serverConnected={true}
        apiUrl="http://localhost"
      />
    );
    expect(screen.getByRole('link', { name: /chat/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /browse resources/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /rag/i })).toBeInTheDocument();
  });

  test('handles navigation link clicks', () => {
    render(
      <SBANavigation
        activeTab="chat"
        onTabChange={mockOnTabChange}
        serverConnected={true}
        apiUrl="http://localhost"
      />
    );
    const loansLink = screen.getByRole('link', { name: /browse resources/i });
    fireEvent.click(loansLink);
    expect(mockOnTabChange).toHaveBeenCalledWith('browse');
  });

  test('shows active navigation state', () => {
    render(
      <SBANavigation
        activeTab="chat"
        onTabChange={mockOnTabChange}
        serverConnected={true}
        apiUrl="http://localhost"
      />
    );
    const chatLink = screen.getByRole('link', { name: /chat/i });
    expect(chatLink).toHaveClass('active');
  });
});
