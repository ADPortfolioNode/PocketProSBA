import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import LoadingBar from '../LoadingBar';
import { ErrorState, AsyncContent } from '../AsyncState';

describe('LoadingBar', () => {
  test('renders an accessible candy-stripe progress bar with a label', () => {
    render(<LoadingBar label="Loading SBA resources…" />);
    const bar = screen.getByRole('progressbar', { name: /Loading SBA resources/i });
    expect(bar).toHaveAttribute('aria-busy', 'true');
    expect(bar.querySelector('.pp-loading-bar__fill')).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent('Loading SBA resources…');
  });

  test('switches to the slow copy when the request is taking a while', () => {
    render(<LoadingBar label="Loading…" slow />);
    expect(screen.getByText(/service may be waking up/i)).toBeInTheDocument();
  });

  test('inline variant renders the small pinwheel, not a bar', () => {
    render(<LoadingBar inline label="Signing in…" />);
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    expect(screen.getByTestId('loading-inline')).toHaveTextContent('Signing in…');
  });
});

describe('ErrorState / AsyncContent', () => {
  test('ErrorState shows friendly copy and a working Retry button', () => {
    const onRetry = jest.fn();
    render(<ErrorState message="We couldn't reach PocketPro." onRetry={onRetry} />);
    expect(screen.getByRole('alert')).toHaveTextContent("We couldn't reach PocketPro.");
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  test('AsyncContent: loading shows the loader and never an error', () => {
    render(<AsyncContent status="loading" error="stale error" loadingLabel="Loading programs…"><p>data</p></AsyncContent>);
    expect(screen.getByRole('progressbar', { name: /Loading programs/i })).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.queryByText('data')).not.toBeInTheDocument();
  });

  test('AsyncContent: error shows ErrorState with Retry; success shows children', () => {
    const onRetry = jest.fn();
    const { rerender } = render(
      <AsyncContent status="error" error="Something went wrong on our side." onRetry={onRetry}><p>data</p></AsyncContent>
    );
    expect(screen.getByRole('alert')).toHaveTextContent('Something went wrong on our side.');
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(onRetry).toHaveBeenCalled();

    rerender(<AsyncContent status="success" onRetry={onRetry}><p>data</p></AsyncContent>);
    expect(screen.getByText('data')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});
