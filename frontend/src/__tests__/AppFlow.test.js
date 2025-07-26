import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import MainLayout from '../components/MainLayout';
import Login from '../Login';

beforeAll(() => {
  // Mock window.alert to avoid not implemented error in tests
  window.alert = jest.fn();
});

describe('Frontend Application Flow Tests', () => {
  test('Navigation tabs switch content correctly', async () => {
    render(
      <MemoryRouter>
        <MainLayout />
      </MemoryRouter>
    );

    // Check initial tab is chat
    const chatTabs = screen.getAllByText(/Chat/i);
    expect(chatTabs[0]).toHaveClass('active');
    expect(chatTabs[0]).toBeInTheDocument();

    // Click Browse Resources tab
    fireEvent.click(screen.getByText(/Browse Resources/i));
    await waitFor(() => {
      expect(screen.getByText(/Browse Resources/i)).toHaveClass('active');
    });

    // Click RAG tab
    fireEvent.click(screen.getByText(/RAG/i));
    await waitFor(() => {
      expect(screen.getByText(/RAG/i)).toHaveClass('active');
    });

    // Click Document Center tab
    fireEvent.click(screen.getByText(/Document Center/i));
    await waitFor(() => {
      expect(screen.getByText(/Document Center/i)).toHaveClass('active');
    });

    // Click SBA Content tab
    fireEvent.click(screen.getByText(/SBA Content/i));
    await waitFor(() => {
      expect(screen.getByText(/SBA Content/i)).toHaveClass('active');
    });
  });

  test('Login page renders and handles form submission', async () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    );

    // Check login form elements
    expect(screen.getByLabelText(/Email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Log In/i })).toBeInTheDocument();

    // Simulate invalid login submission
    fireEvent.change(screen.getByLabelText(/Email address/i), { target: { value: 'invalidUser' } });
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'wrongPass' } });
    fireEvent.click(screen.getByRole('button', { name: /Log In/i }));

    // Expect error message or validation (adjust based on actual implementation)
    await waitFor(() => {
      expect(screen.getByText(/Invalid credentials/i)).toBeInTheDocument();
    });

    // Simulate valid login submission (adjust credentials as needed)
    fireEvent.change(screen.getByLabelText(/Email address/i), { target: { value: 'validUser' } });
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'correctPass' } });
    fireEvent.click(screen.getByRole('button', { name: /Log In/i }));

    // Expect redirect or success message (adjust based on actual implementation)
    await waitFor(() => {
      expect(screen.queryByText(/Invalid credentials/i)).not.toBeInTheDocument();
    });
  });
});
