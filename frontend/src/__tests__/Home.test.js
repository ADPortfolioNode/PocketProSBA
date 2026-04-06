import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Home from '../components/Home';

describe('Home Component', () => {
  test('renders Home component content with hero overview', () => {
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    );
    expect(screen.getByText(/simplified sba guidance for small business success/i)).toBeInTheDocument();
    expect(screen.getByText(/current sba status/i)).toBeInTheDocument();
    expect(screen.getByText(/use case suggestions/i)).toBeInTheDocument();
  });
});
