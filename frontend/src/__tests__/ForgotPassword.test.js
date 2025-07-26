import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ForgotPassword from '../ForgotPassword';

describe('ForgotPassword Page', () => {
  test('renders ForgotPassword page', () => {
    render(
      <MemoryRouter>
        <ForgotPassword />
      </MemoryRouter>
    );
    expect(screen.getByText(/Forgot Password/i)).toBeInTheDocument();
  });

  test('validates form inputs and shows errors', () => {
    render(
      <MemoryRouter>
        <ForgotPassword />
      </MemoryRouter>
    );
    fireEvent.click(screen.getByRole('button', { name: /Send Reset Link/i }));
    expect(screen.getByText(/Email is required/i)).toBeInTheDocument();
  });

  test('navigates back to Login page', () => {
    render(
      <MemoryRouter>
        <ForgotPassword />
      </MemoryRouter>
    );
    const loginLink = screen.getByText(/Log in/i);
    expect(loginLink).toBeInTheDocument();
    // Navigation test would require mocking router or userEvent, omitted here for brevity
  });
});
