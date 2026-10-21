import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter, Routes, Route, useLocation } from 'react-router-dom';
import SBANavigation from './SBANavigation';

// The status badge polls the backend on its own; keep it offline-quiet in unit tests.
jest.mock('../services/connectionService', () => ({
  __esModule: true,
  default: { checkConnection: jest.fn().mockResolvedValue({ connected: true, data: {} }) },
}));

const Where = () => <div data-testid="where">{useLocation().pathname}</div>;

const renderNav = (route = '/chat') =>
  render(
    <MemoryRouter initialEntries={[route]}>
      <SBANavigation serverConnected={true} apiUrl={(p) => `http://localhost${p}`} />
      <Routes>
        <Route path="*" element={<Where />} />
      </Routes>
    </MemoryRouter>
  );

describe('SBANavigation', () => {
  test('renders navigation menu', () => {
    renderNav();
    expect(screen.getByRole('navigation', { name: /Primary/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /^Chat$/i })).toBeInTheDocument();
  });

  test('displays navigation links', () => {
    renderNav();
    expect(screen.getByRole('link', { name: /^chat$/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /resources/i })).toHaveAttribute('href', '/browse');
    expect(screen.getByRole('link', { name: /^rag$/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /programs/i })).toHaveAttribute('href', '/sba');
  });

  test('handles navigation link clicks', () => {
    renderNav('/chat');
    fireEvent.click(screen.getByRole('link', { name: /^rag$/i }));
    expect(screen.getByTestId('where')).toHaveTextContent('/rag');
  });

  test('shows active navigation state', () => {
    renderNav('/chat');
    const chatLink = screen.getByRole('link', { name: /^chat$/i });
    expect(chatLink).toHaveClass('is-active');
    expect(chatLink).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('link', { name: /^home$/i })).not.toHaveClass('is-active');
  });
});
