import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ErrorBoundary from '../ErrorBoundary';

function Boom({ explode }) {
  if (explode) throw new Error('kaboom: secret stack detail');
  return <p>All good</p>;
}

describe('ErrorBoundary', () => {
  beforeEach(() => {
    // React logs caught render errors; keep the test output clean.
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });
  afterEach(() => console.error.mockRestore());

  test('renders children when nothing throws', () => {
    render(<ErrorBoundary><Boom /></ErrorBoundary>);
    expect(screen.getByText('All good')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  test('a render error shows the friendly card with Reload, not the raw error', () => {
    const onReload = jest.fn();
    render(<ErrorBoundary onReload={onReload}><Boom explode /></ErrorBoundary>);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent(/Something went wrong/i);
    expect(alert).toHaveTextContent(/Reloading usually fixes it/i);
    expect(alert).not.toHaveTextContent(/kaboom/);
    expect(alert.closest('.pp-error-state')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Reload' }));
    expect(onReload).toHaveBeenCalledTimes(1);
  });

  test('changing resetKey (e.g. switching tabs) clears the error', () => {
    const { rerender } = render(<ErrorBoundary resetKey="rag"><Boom explode /></ErrorBoundary>);
    expect(screen.getByRole('alert')).toBeInTheDocument();
    rerender(<ErrorBoundary resetKey="chat"><Boom /></ErrorBoundary>);
    expect(screen.getByText('All good')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});
