import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SBAContentExplorer from './SBAContentExplorer';
import apiClient from '../api/apiClient';

jest.mock('../api/apiClient');

// The explorer builds its nav from GET /api/sba/resources, then auto-opens
// "SBA Loans" (or the first entry) by GETting that resource's path.
const catalog = {
  resources: [
    { id: 'loans', name: 'SBA Loans', path: '/api/sba/content/loans', group: 'Funding' },
    { id: 'articles', name: 'Articles', path: '/api/sba/content/articles', group: 'Learn' },
  ],
};
const loanItems = {
  items: [
    { id: '7a', title: '7(a) loans', description: 'Primary SBA loan program' },
    { id: 'microloans', title: 'Microloans', description: 'Up to $50,000' },
  ],
  totalPages: 1,
  currentPage: 1,
  is_current: true,
  source: 'live',
};

const mockGet = ({ catalogData = catalog, itemsData = loanItems } = {}) =>
  apiClient.get.mockImplementation((url) => {
    if (url === '/api/sba/resources') return Promise.resolve({ data: catalogData });
    if (url === '/api/sba/content/loans') return Promise.resolve({ data: itemsData });
    return Promise.resolve({ data: {} });
  });

describe('SBAContentExplorer', () => {
  beforeEach(() => {
    apiClient.get.mockReset();
  });

  test('renders content explorer interface and loads the resource catalog', async () => {
    mockGet();
    render(<SBAContentExplorer />);

    expect(screen.getByRole('heading', { name: /SBA Resources/i })).toBeInTheDocument();

    await waitFor(() => {
      expect(apiClient.get).toHaveBeenCalledWith('/api/sba/resources', {}, { quiet: true });
    });
    // Nav entries come from the catalog, and SBA Loans opens automatically
    expect(await screen.findByText('7(a) loans')).toBeInTheDocument();
    expect(screen.getByText('Microloans')).toBeInTheDocument();
    expect(screen.getAllByText('Articles').length).toBeGreaterThanOrEqual(1);
    expect(apiClient.get).toHaveBeenCalledWith(
      '/api/sba/content/loans',
      expect.objectContaining({ params: { query: undefined, page: 1 } }),
      { quiet: true }
    );
  });

  test('handles search input updates', async () => {
    mockGet();
    render(<SBAContentExplorer />);
    await screen.findByText('7(a) loans');

    const searchInput = screen.getByPlaceholderText(/Search SBA Loans/i);
    fireEvent.change(searchInput, { target: { value: 'SBA loans' } });
    expect(searchInput.value).toBe('SBA loans');

    fireEvent.click(screen.getByRole('button', { name: /^Search$/i }));
    await waitFor(() =>
      expect(apiClient.get).toHaveBeenCalledWith(
        '/api/sba/content/loans',
        expect.objectContaining({ params: { query: 'SBA loans', page: 1 } }),
        { quiet: true }
      )
    );
  });

  test('shows a notice when the catalog is empty', async () => {
    mockGet({ catalogData: { resources: [] } });
    render(<SBAContentExplorer />);
    expect(await screen.findByText(/No resources returned/i)).toBeInTheDocument();
  });
});
