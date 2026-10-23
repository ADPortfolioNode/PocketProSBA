import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import apiClient from '../../api/apiClient';
import UploadsManager, { DOCUMENTS_LIST_ENDPOINT } from '../UploadsManager';

jest.mock('../../api/apiClient');

const ok = (data) => Promise.resolve({ data, status: 200 });

describe('UploadsManager (Docs tab)', () => {
  test('loads the file list from /api/documents/list when mounted without props', async () => {
    apiClient.get.mockImplementation(() => ok({ files: [{ filename: 'plan.txt', size: 2048 }] }));
    render(<UploadsManager />);

    // Candy-stripe loader while the list loads, never an error.
    expect(screen.getByRole('progressbar', { name: /Loading your documents/i })).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();

    expect(await screen.findByText('plan.txt')).toBeInTheDocument();
    expect(screen.getByText('(2 KB)')).toBeInTheDocument();
    expect(apiClient.get).toHaveBeenCalledWith(DOCUMENTS_LIST_ENDPOINT, {}, { quiet: true });
  });

  test('shows the empty state when the backend has no files', async () => {
    apiClient.get.mockImplementation(() => ok({ files: [] }));
    render(<UploadsManager />);
    expect(await screen.findByText(/No files uploaded yet/i)).toBeInTheDocument();
  });

  test('Refresh List re-fetches the list', async () => {
    apiClient.get
      .mockImplementationOnce(() => ok({ files: [] }))
      .mockImplementationOnce(() => ok({ files: [{ filename: 'new.md', size: 10 }] }));
    render(<UploadsManager />);
    await screen.findByText(/No files uploaded yet/i);

    fireEvent.click(screen.getByRole('button', { name: /Refresh List/i }));
    expect(await screen.findByText('new.md')).toBeInTheDocument();
    expect(apiClient.get).toHaveBeenCalledTimes(2);
  });

  test('a failed load shows a friendly error with Retry, and Retry recovers', async () => {
    jest.spyOn(console, 'error').mockImplementation(() => {});
    apiClient.get
      .mockImplementationOnce(() => Promise.reject(Object.assign(new Error('Request failed with status code 500'), { response: { status: 500 } })))
      .mockImplementationOnce(() => ok({ files: [{ filename: 'back.txt', size: 1024 }] }));
    render(<UploadsManager />);

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/Couldn't load your documents/i);
    expect(alert).not.toHaveTextContent(/status code 500/);

    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(await screen.findByText('back.txt')).toBeInTheDocument();
    console.error.mockRestore();
  });

  test('controlled mode uses the files prop and onRefresh, and does not fetch', () => {
    const onRefresh = jest.fn();
    render(<UploadsManager files={[{ filename: 'given.pdf', size: 4096 }]} onRefresh={onRefresh} />);
    expect(screen.getByText('given.pdf')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Refresh List/i }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
    expect(apiClient.get).not.toHaveBeenCalled();
  });

  test('the file input has an accessible name', async () => {
    apiClient.get.mockImplementation(() => ok({ files: [] }));
    render(<UploadsManager />);
    const input = screen.getByLabelText(/Choose a document to upload/i);
    expect(input).toHaveAttribute('type', 'file');
    await screen.findByText(/No files uploaded yet/i);
  });

  test('a successful upload reloads the list', async () => {
    apiClient.get
      .mockImplementationOnce(() => ok({ files: [] }))
      .mockImplementationOnce(() => ok({ files: [{ filename: 'up.txt', size: 5 }] }));
    const originalFetch = global.fetch;
    global.fetch = jest.fn(() => Promise.resolve({ ok: true, status: 200 }));
    try {
      render(<UploadsManager />);
      await screen.findByText(/No files uploaded yet/i);
      const file = new File(['hello'], 'up.txt', { type: 'text/plain' });
      fireEvent.change(screen.getByLabelText(/Choose a document to upload/i), { target: { files: [file] } });
      fireEvent.click(screen.getByRole('button', { name: 'Upload' }));

      expect(await screen.findByText('up.txt')).toBeInTheDocument();
      expect(global.fetch).toHaveBeenCalledWith(expect.stringMatching(/\/api\/documents\/upload$/), expect.objectContaining({ method: 'POST' }));
      await waitFor(() => expect(apiClient.get).toHaveBeenCalledTimes(2));
    } finally {
      global.fetch = originalFetch;
    }
  });
});
