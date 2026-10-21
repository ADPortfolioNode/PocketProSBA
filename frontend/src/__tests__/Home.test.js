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
    expect(screen.getByRole('heading', { name: /Funding guidance built for small business/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /^Services$/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Popular questions/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Current SBA loan programs/i })).toBeInTheDocument();
  });

  test('links to chat and the live resources page', () => {
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    );
    expect(screen.getByRole('link', { name: /Start chat/i })).toHaveAttribute('href', '/chat');
    expect(screen.getByRole('link', { name: /Browse resources/i })).toHaveAttribute('href', '/browse');
  });
});
