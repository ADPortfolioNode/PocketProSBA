import React from 'react';
import { screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import ResetPassword from '../ResetPassword';
import ForgotPassword from '../ForgotPassword';
import apiClient from '../api/apiClient';
import { renderWithProviders, healthyGet, axiosResponse } from '../test-utils';

jest.mock('../api/apiClient');

const renderAt = (entry) =>
  renderWithProviders(
    <MemoryRouter initialEntries={[entry]}>
      <Routes>
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/login" element={<div>Login page</div>} />
      </Routes>
    </MemoryRouter>,
    { withRouter: false }
  );

const fill = (password, confirm) => {
  fireEvent.change(screen.getByLabelText(/^New password/i), { target: { value: password } });
  fireEvent.change(screen.getByLabelText(/Confirm new password/i), { target: { value: confirm } });
  fireEvent.click(screen.getByRole('button', { name: /Update Password/i }));
};

describe('ResetPassword Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    apiClient.get.mockImplementation(healthyGet);
  });

  test('renders with the token from the URL (no token field)', () => {
    renderAt('/reset-password?token=abc123');
    expect(screen.getByRole('heading', { name: /Reset Password/i })).toBeInTheDocument();
    expect(screen.queryByLabelText(/Reset token/i)).not.toBeInTheDocument();
  });

  test('enforces 8+ characters', () => {
    renderAt('/reset-password?token=abc123');
    fill('short', 'short');
    expect(screen.getByText(/at least 8 characters/i)).toBeInTheDocument();
    expect(apiClient.post).not.toHaveBeenCalled();
  });

  test('requires the confirmation to match', () => {
    renderAt('/reset-password?token=abc123');
    fill('longenough1', 'longenough2');
    expect(screen.getByText(/Passwords do not match/i)).toBeInTheDocument();
    expect(apiClient.post).not.toHaveBeenCalled();
  });

  test('posts token + password and shows success with a login link', async () => {
    apiClient.post.mockResolvedValueOnce(axiosResponse({ success: true }));
    renderAt('/reset-password?token=abc123');
    fill('longenough1', 'longenough1');

    expect(await screen.findByText(/password has been updated/i)).toBeInTheDocument();
    expect(apiClient.post).toHaveBeenCalledWith('/api/auth/reset-password', {
      token: 'abc123',
      password: 'longenough1',
    });
    fireEvent.click(screen.getByRole('link', { name: /Log in with your new password/i }));
    expect(screen.getByText('Login page')).toBeInTheDocument();
  });

  test('shows the server error for an invalid token', async () => {
    apiClient.post.mockRejectedValueOnce({
      response: { status: 400, data: { error: 'Invalid or expired reset token' } },
    });
    renderAt('/reset-password?token=bad');
    fill('longenough1', 'longenough1');
    expect(await screen.findByText(/Invalid or expired reset token/i)).toBeInTheDocument();
  });

  test('asks for the token when the URL has none', () => {
    renderAt('/reset-password');
    fill('longenough1', 'longenough1');
    expect(screen.getByText(/Reset token is missing/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Reset token/i)).toBeInTheDocument();
  });

  test('forgot-password page links to the reset page', () => {
    renderAt('/forgot-password');
    fireEvent.click(screen.getByRole('link', { name: /Set a new password/i }));
    expect(screen.getByRole('heading', { name: /Reset Password/i })).toBeInTheDocument();
  });
});
