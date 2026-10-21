import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import Register from '../Register';
import apiClient from '../api/apiClient';
import { renderWithProviders, healthyGet, axiosResponse } from '../test-utils';

jest.mock('../api/apiClient');

const renderRegister = () =>
  renderWithProviders(
    <MemoryRouter initialEntries={['/register']}>
      <Routes>
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<div>Login page</div>} />
      </Routes>
    </MemoryRouter>,
    { withRouter: false }
  );

const fill = (label, value) => fireEvent.change(screen.getByLabelText(label), { target: { value } });

describe('Register Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    apiClient.get.mockImplementation(healthyGet);
    window.alert = jest.fn();
  });

  test('renders Register page', () => {
    renderRegister();
    expect(screen.getByRole('heading', { name: /Register/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign Up/i })).toBeInTheDocument();
  });

  test('validates form inputs and shows errors', () => {
    renderRegister();
    fireEvent.click(screen.getByRole('button', { name: /Sign Up/i }));
    expect(screen.getByText(/All fields are required/i)).toBeInTheDocument();

    fill(/Email address/i, 'a@b.co');
    fill(/^Password$/i, 'secret1');
    fill(/Confirm Password/i, 'secret2');
    fireEvent.click(screen.getByRole('button', { name: /Sign Up/i }));
    expect(screen.getByText(/Passwords do not match/i)).toBeInTheDocument();
    expect(apiClient.post).not.toHaveBeenCalled();
  });

  test('navigates back to Login page', () => {
    renderRegister();
    fireEvent.click(screen.getByRole('link', { name: /Log in/i }));
    expect(screen.getByText('Login page')).toBeInTheDocument();
  });

  test('registers and sends the user to Login', async () => {
    apiClient.post.mockResolvedValueOnce(axiosResponse({ ok: true }));
    renderRegister();
    fill(/Email address/i, 'a@b.co');
    fill(/^Password$/i, 'secret1');
    fill(/Confirm Password/i, 'secret1');
    fireEvent.click(screen.getByRole('button', { name: /Sign Up/i }));
    expect(await screen.findByText('Login page')).toBeInTheDocument();
    await waitFor(() => expect(apiClient.post).toHaveBeenCalledWith('/api/register', expect.objectContaining({ email: 'a@b.co', password: 'secret1' })));
  });
});
