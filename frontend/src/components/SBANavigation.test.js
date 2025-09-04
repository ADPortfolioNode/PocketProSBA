import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import SBANavigation from './SBANavigation';

describe('SBANavigation', () => {
  test('renders navigation menu', () => {
    render(<SBANavigation />);
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getByText(/home/i)).toBeInTheDocument();
  });

  test('displays navigation links', () => {
    render(<SBANavigation />);
    expect(screen.getByRole('link', { name: /loans/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /grants/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /resources/i })).toBeInTheDocument();
  });

  test('handles navigation link clicks', () => {
    render(<SBANavigation />);
    const loansLink = screen.getByRole('link', { name: /loans/i });
    fireEvent.click(loansLink);
    // Add assertion for navigation behavior
  });

  test('shows active navigation state', () => {
    render(<SBANavigation currentPath="/loans" />);
    const loansLink = screen.getByRole('link', { name: /loans/i });
    expect(loansLink).toHaveClass('active');
  });
});
