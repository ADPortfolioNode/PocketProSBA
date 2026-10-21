import React from 'react';
import { screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import ForgotPassword from '../ForgotPassword';
import apiClient from '../api/apiClient';
import { renderWithProviders, healthyGet, axiosResponse } from '../test-utils';

jest.mock('../api/apiClient');

const renderPage = () =>
  renderWithProviders(
    <MemoryRouter initialEntries={['/forgot-password']}>
      <Routes>
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/login" element={<div>Login page</div>} />
      </Routes>
    </MemoryRouter>,
    { withRouter: false }
  );

describe('ForgotPassword Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    apiClient.get.mockImplementation(healthyGet);
  });

  test('renders ForgotPassword page', () => {
    renderPage();
    expect(screen.getByRole('heading', { name: /Forgot Password/i })).toBeInTheDocument();
  });

  test('validates form inputs and shows errors', () => {
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: /Send Reset Link/i }));
    expect(screen.getByText(/Email is required/i)).toBeInTheDocument();
    expect(apiClient.post).not.toHaveBeenCalled();
  });

  test('navigates back to Login page', () => {
    renderPage();
    fireEvent.click(screen.getByRole('link', { name: /Log in/i }));
    expect(screen.getByText('Login page')).toBeInTheDocument();
  });

  test('shows a neutral confirmation after requesting a reset', async () => {
    apiClient.post.mockResolvedValueOnce(axiosResponse({ ok: true }));
    renderPage();
    fireEvent.change(screen.getByLabelText(/Email address/i), { target: { value: 'a@b.co' } });
    fireEvent.click(screen.getByRole('button', { name: /Send Reset Link/i }));
    expect(await screen.findByText(/you will receive password reset instructions/i)).toBeInTheDocument();
  });
});
