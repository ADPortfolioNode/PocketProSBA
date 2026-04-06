import React from 'react';
import { render, fireEvent, waitFor, screen } from '@testing-library/react';
import RAGWorkflowInterface from './RAGWorkflowInterface';
import apiClient from '../api/apiClient';

jest.mock('../api/apiClient');

describe('RAGWorkflowInterface', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders upload step and allows file selection', () => {
    render(<RAGWorkflowInterface documents={[]} searchResults={[]} ragResponse={null} />);
    expect(screen.getByText(/Upload Document/i)).toBeInTheDocument();
    const fileInput = screen.getByLabelText(/Select a file to upload/i);
    expect(fileInput).toBeInTheDocument();
  });

  it('decomposes a task and displays steps', async () => {
    apiClient.post.mockResolvedValueOnce({ response: { steps: [{ instruction: 'Step 1' }, { instruction: 'Step 2' }] } });
    render(<RAGWorkflowInterface documents={[]} searchResults={[]} ragResponse={null} />);
    fireEvent.click(screen.getByText(/Start Task Without Upload/i));
    fireEvent.change(screen.getByPlaceholderText(/Find SBA loan options/i), { target: { value: 'Find SBA loan options' } });
    fireEvent.click(screen.getByRole('button', { name: /Decompose Task/i }));
    await waitFor(() => expect(screen.getByText(/Step 1/i)).toBeInTheDocument());
    expect(screen.getByText(/Step 2/i)).toBeInTheDocument();
  });

  it('executes a step and displays result', async () => {
    apiClient.post.mockResolvedValueOnce({ response: { steps: [{ instruction: 'Step 1' }] } });
    apiClient.post.mockResolvedValueOnce({ result: 'Executed Step 1' });
    render(<RAGWorkflowInterface documents={[]} searchResults={[]} ragResponse={null} />);
    fireEvent.click(screen.getByText(/Start Task Without Upload/i));
    fireEvent.change(screen.getByPlaceholderText(/Find SBA loan options/i), { target: { value: 'Find SBA loan options' } });
    fireEvent.click(screen.getByRole('button', { name: /Decompose Task/i }));
    await waitFor(() => screen.getByText(/Step 1/i));
    fireEvent.click(screen.getByText(/Execute Step 1/i));
    await waitFor(() => expect(screen.getByText(/Executed Step 1/i)).toBeInTheDocument());
  });

  it('validates a step and displays feedback', async () => {
    apiClient.post.mockResolvedValueOnce({ response: { steps: [{ instruction: 'Step 1' }] } });
    apiClient.post.mockResolvedValueOnce({ result: 'Executed Step 1' });
    apiClient.post.mockResolvedValueOnce({ status: 'PASS', feedback: 'Step validated' });
    render(<RAGWorkflowInterface documents={[]} searchResults={[]} ragResponse={null} />);
    fireEvent.click(screen.getByText(/Start Task Without Upload/i));
    fireEvent.change(screen.getByPlaceholderText(/Find SBA loan options/i), { target: { value: 'Find SBA loan options' } });
    fireEvent.click(screen.getByRole('button', { name: /Decompose Task/i }));
    await waitFor(() => screen.getByText(/Step 1/i));
    fireEvent.click(screen.getByText(/Execute Step 1/i));
    await waitFor(() => screen.getByText(/Executed Step 1/i));
    fireEvent.click(screen.getByText(/Validate Steps/i));
    fireEvent.click(screen.getByText(/Validate Step 1/i));
    await waitFor(() => expect(screen.getByText(/Step validated/i)).toBeInTheDocument());
  });

  it('queries documents and displays results', async () => {
    apiClient.post.mockImplementation((url) => {
      if (url === '/api/decompose') {
        return Promise.resolve({ response: { steps: [{ instruction: 'Step 1' }] } });
      }
      if (url === '/api/execute') {
        return Promise.resolve({ result: 'Executed Step 1' });
      }
      if (url === '/api/validate') {
        return Promise.resolve({ status: 'PASS', feedback: 'Step validated' });
      }
      if (url === '/api/query') {
        return Promise.resolve({ results: [{ content: 'Relevant doc' }] });
      }
      return Promise.reject(new Error(`Unexpected API call to ${url}`));
    });

    const { container } = render(<RAGWorkflowInterface documents={[]} searchResults={[]} ragResponse={null} />);
    fireEvent.click(screen.getByText(/Start Task Without Upload/i));
    fireEvent.change(screen.getByPlaceholderText(/Find SBA loan options/i), { target: { value: 'Find SBA loan options' } });
    fireEvent.click(screen.getByRole('button', { name: /Decompose Task/i }));
    await waitFor(() => screen.getByText(/Step 1/i));
    fireEvent.click(screen.getByText(/Execute Step 1/i));
    await waitFor(() => screen.getByText(/Executed Step 1/i));
    fireEvent.click(screen.getByText(/Validate Steps/i));
    fireEvent.click(screen.getByText(/Validate Step 1/i));
    await waitFor(() => screen.getByText(/Step validated/i));
    fireEvent.click(screen.getByText(/Query Documents/i));
    fireEvent.change(screen.getByPlaceholderText(/What types of SBA loans/i), { target: { value: 'What types of SBA loans are available?' } });
    const form = container.querySelector('form');
    fireEvent.submit(form);
    await waitFor(() => expect(apiClient.post).toHaveBeenCalledWith('/api/query', { query: 'What types of SBA loans are available?', top_k: 5 }));
    await waitFor(() => screen.getByRole('button', { name: /Generate Final Answer/i }));
    fireEvent.click(screen.getByRole('button', { name: /Generate Final Answer/i }));
    await waitFor(() => expect(screen.getByText(/AI-generated answer based on validated steps and retrieved context\./i)).toBeInTheDocument());
  });
});
