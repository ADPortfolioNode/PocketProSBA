import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import Login from '../Login';
import apiClient from '../api/apiClient';
import { renderWithProviders, healthyGet, axiosResponse } from '../test-utils';

jest.mock('../api/apiClient');

const renderLogin = () =>
  renderWithProviders(
    <MemoryRouter initialEntries={['/login']}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<div>Home page</div>} />
      </Routes>
    </MemoryRouter>,
    { withRouter: false }
  );

describe('Login Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    apiClient.get.mockImplementation(healthyGet);
    window.alert = jest.fn();
  });

  test('renders email and password inputs and login button', () => {
    renderLogin();
    expect(screen.getByLabelText(/Email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Log In/i })).toBeInTheDocument();
  });

  test('shows validation errors when submitting empty form', async () => {
    renderLogin();
    fireEvent.click(screen.getByRole('button', { name: /Log In/i }));
    expect(await screen.findByText(/Both email and password are required/i)).toBeInTheDocument();
    expect(apiClient.post).not.toHaveBeenCalled();
  });

  test('navigates to home page on successful login', async () => {
    apiClient.post.mockResolvedValueOnce(axiosResponse({ user: { email: 'test@example.com' }, token: 't' }));
    renderLogin();

    fireEvent.change(screen.getByLabelText(/Email address/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /Log In/i }));

    expect(await screen.findByText('Home page')).toBeInTheDocument();
    // Remember me is on by default, so login sends remember_me: true.
    expect(apiClient.post).toHaveBeenCalledWith('/api/login', { email: 'test@example.com', password: 'password123', remember_me: true });
  });

  test('shows the server error message when login fails', async () => {
    apiClient.post.mockRejectedValueOnce({ response: { status: 401, data: { error: 'Invalid credentials' } } });
    renderLogin();

    fireEvent.change(screen.getByLabelText(/Email address/i), { target: { value: 'a@b.co' } });
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'nope' } });
    fireEvent.click(screen.getByRole('button', { name: /Log In/i }));

    expect(await screen.findByText(/Invalid credentials/i)).toBeInTheDocument();
  });
});
