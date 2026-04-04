import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SBAContentExplorer from './SBAContentExplorer';
import apiClient from '../api/apiClient';

jest.mock('../api/apiClient');

describe('SBAContentExplorer', () => {
  beforeEach(() => {
    apiClient.get.mockReset();
  });

  test('renders content explorer interface and calls health endpoints', async () => {
    apiClient.get
      .mockResolvedValueOnce({ data: { status: 'healthy', message: 'Flask OK' } })
      .mockResolvedValueOnce({ data: { status: 'ok', message: 'Chroma OK' } });

    render(<SBAContentExplorer />);

    expect(screen.getByRole('searchbox')).toBeInTheDocument();
    expect(screen.getByText(/sba content explorer/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(apiClient.get).toHaveBeenNthCalledWith(1, '/api/health', {}, { quiet: true });
      expect(apiClient.get).toHaveBeenNthCalledWith(2, '/api/chromadb_health', {}, { quiet: true });
    });

    expect(screen.getAllByText(/online/i).length).toBeGreaterThanOrEqual(1);
  });

  test('handles search input updates', async () => {
    apiClient.get.mockResolvedValueOnce({ data: { status: 'healthy' } });
    render(<SBAContentExplorer />);

    await waitFor(() => {
      expect(apiClient.get).toHaveBeenCalled();
    });

    const searchInput = screen.getByRole('searchbox');
    fireEvent.change(searchInput, { target: { value: 'SBA loans' } });

    expect(searchInput.value).toBe('SBA loans');
  });
});
