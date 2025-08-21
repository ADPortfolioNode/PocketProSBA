import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ServerStatusMonitor from '../ServerStatusMonitor';
import apiClient from '../../../api/apiClient';

jest.mock('../../../api/apiClient');

describe('ServerStatusMonitor', () => {
  it('should show online status when api call is successful', async () => {
    apiClient.get.mockResolvedValue({ data: { status: 'ok' } });
    render(<ServerStatusMonitor />);
    await waitFor(() => {
      expect(screen.getByText(/Server Connected/i)).toBeInTheDocument();
    });
  });

  it('should show offline status when api call fails', async () => {
    apiClient.get.mockRejectedValue(new Error('Network Error'));
    render(<ServerStatusMonitor />);
    await waitFor(() => {
      expect(screen.getByText(/Server Unavailable/i)).toBeInTheDocument();
    });
  });
});
