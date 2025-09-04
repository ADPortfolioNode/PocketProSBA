import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import Footer from './Footer';

describe('Footer', () => {
  test('renders footer content', () => {
    render(<Footer />);
    expect(screen.getByRole('contentinfo')).toBeInTheDocument();
  });

  test('displays copyright information', () => {
    render(<Footer />);
    expect(screen.getByText(/©/i)).toBeInTheDocument();
    expect(screen.getByText(/2024/i)).toBeInTheDocument();
  });

  test('shows contact information', () => {
    render(<Footer />);
    expect(screen.getByText(/contact/i)).toBeInTheDocument();
  });

  test('displays social media links', () => {
    render(<Footer />);
    expect(screen.getAllByRole('link')).toHaveLength(3); // Assuming 3 social links
  });
});
