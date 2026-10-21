import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import Footer from './Footer';

// The footer is a slim brand strip (name + tagline). The old copyright/contact/
// social-link assertions described a footer that no longer exists.
describe('Footer', () => {
  test('renders footer content', () => {
    render(<Footer />);
    expect(screen.getByRole('contentinfo')).toBeInTheDocument();
  });

  test('displays the brand name', () => {
    render(<Footer />);
    expect(screen.getByText('PocketPro SBA')).toBeInTheDocument();
  });

  test('shows the tagline', () => {
    render(<Footer />);
    expect(screen.getByText(/Small business guidance/i)).toBeInTheDocument();
  });

  test('has no links (purely informational)', () => {
    render(<Footer />);
    expect(screen.queryAllByRole('link')).toHaveLength(0);
  });
});
