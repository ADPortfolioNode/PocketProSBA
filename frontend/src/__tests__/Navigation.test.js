import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import App from '../App';

describe('Main Navigation', () => {
  test('navigates between pages', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );

    // Verify Home page content
    expect(screen.getByText(/Home/i)).toBeInTheDocument();

    // Navigate to Login page
    const loginLink = screen.getByText(/Login/i);
    await userEvent.click(loginLink);
    expect(screen.getByText(/Login/i)).toBeInTheDocument();

    // Navigate to Register page
    const registerLink = screen.getByText(/Register/i);
    await userEvent.click(registerLink);
    expect(screen.getByText(/Register/i)).toBeInTheDocument();

    // Navigate to Forgot Password page
    const forgotPasswordLink = screen.getByText(/Forgot Password/i);
    await userEvent.click(forgotPasswordLink);
    expect(screen.getByText(/Forgot Password/i)).toBeInTheDocument();
  });
});
