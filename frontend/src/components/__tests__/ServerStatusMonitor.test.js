import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ServerStatusMonitor from '../ServerStatusMonitor';
import apiClient from '../../api/apiClient';

jest.mock('../../api/apiClient');

describe('ServerStatusMonitor', () => {
  beforeEach(() => jest.clearAllMocks());

  it('should show online status when api call is successful', async () => {
    apiClient.get.mockResolvedValue({ data: { status: 'ok', version: '1.2.3' } });
    render(<ServerStatusMonitor />);
    await waitFor(() => {
      expect(screen.getByText(/Server Connected/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/Version: 1.2.3/)).toBeInTheDocument();
    expect(apiClient.get).toHaveBeenCalledWith('/api/health');
  });

  it('should show offline status when api call fails', async () => {
    jest.spyOn(console, 'error').mockImplementation(() => {});
    apiClient.get.mockRejectedValue(new Error('Network Error'));
    const onStatusChange = jest.fn();
    render(<ServerStatusMonitor onStatusChange={onStatusChange} />);
    await waitFor(() => {
      expect(screen.getByText(/Server Unavailable/i)).toBeInTheDocument();
    });
    expect(onStatusChange).toHaveBeenCalledWith('offline', null);

    apiClient.get.mockResolvedValue({ data: { status: 'ok' } });
    fireEvent.click(screen.getByRole('button', { name: /Retry Connection/i }));
    await waitFor(() => expect(screen.getByText(/Server Connected/i)).toBeInTheDocument());
    console.error.mockRestore();
  });
});
