import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import App from '../App';
import apiClient from '../api/apiClient';
import { healthyGet } from '../test-utils';

jest.mock('../api/apiClient');

// App owns its BrowserRouter, so drive the URL through window.history.
const renderAt = (path) => {
  window.history.pushState({}, '', path);
  return render(<App />);
};

describe('Main Navigation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    apiClient.get.mockImplementation(healthyGet);
  });

  afterAll(() => window.history.pushState({}, '', '/'));

  test('navigates between the auth pages', () => {
    renderAt('/login');
    expect(screen.getByRole('heading', { name: /^Login$/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('link', { name: /Register/i }));
    expect(screen.getByRole('heading', { name: /^Register$/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('link', { name: /Log in/i }));
    expect(screen.getByRole('heading', { name: /^Login$/i })).toBeInTheDocument();
  });

  test('serves the Forgot Password route', () => {
    renderAt('/forgot-password');
    expect(screen.getByRole('heading', { name: /Forgot Password/i })).toBeInTheDocument();
  });

  test('renders the Home shell at / with primary nav', async () => {
    renderAt('/');
    expect(await screen.findByRole('heading', { name: /Funding guidance built for small business/i })).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: /Primary/i })).toBeInTheDocument();
    expect(screen.getByTestId('nav-home')).toHaveClass('is-active');
  });
});
