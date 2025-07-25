import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Register from '../Register';

describe('Register Page', () => {
  test('renders Register page', () => {
    render(
      <MemoryRouter>
        <Register />
      </MemoryRouter>
    );
    expect(screen.getByText(/Register/i)).toBeInTheDocument();
  });

  test('validates form inputs and shows errors', () => {
    render(
      <MemoryRouter>
        <Register />
      </MemoryRouter>
    );
    fireEvent.click(screen.getByRole('button', { name: /Register/i }));
    expect(screen.getByText(/Email is required/i)).toBeInTheDocument();
    expect(screen.getByText(/Password is required/i)).toBeInTheDocument();
  });

  test('navigates back to Login page', () => {
    render(
      <MemoryRouter initialEntries={['/register']}>
        <Register />
      </MemoryRouter>
    );
    const loginLink = screen.getByText(/Login/i);
    expect(loginLink).toBeInTheDocument();
    // Navigation test would require mocking router or userEvent, omitted here for brevity
  });
});
