import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import SBAContentExplorer from './SBAContentExplorer';

describe('SBAContentExplorer', () => {
  test('renders content explorer interface', () => {
    render(<SBAContentExplorer />);
    expect(screen.getByRole('searchbox')).toBeInTheDocument();
    expect(screen.getByText(/sba content/i)).toBeInTheDocument();
  });

  test('displays content categories', () => {
    render(<SBAContentExplorer />);
    expect(screen.getByText(/loans/i)).toBeInTheDocument();
    expect(screen.getByText(/grants/i)).toBeInTheDocument();
  });

  test('handles search functionality', () => {
    render(<SBAContentExplorer />);
    const searchInput = screen.getByRole('searchbox');
    fireEvent.change(searchInput, { target: { value: 'SBA loans' } });
    expect(searchInput.value).toBe('SBA loans');
  });

  test('displays content items', () => {
    render(<SBAContentExplorer />);
    expect(screen.getAllByRole('article')).toHaveLength(3); // Assuming 3 content items
  });
});
