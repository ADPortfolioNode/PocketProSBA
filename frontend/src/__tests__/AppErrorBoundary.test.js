import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('../api/apiClient');
// Make the app shell crash on render: the top-level boundary must catch it.
jest.mock('../components/MainLayout', () => () => {
  throw new Error('layout exploded');
});

const App = require('../App').default;

test('a crash anywhere in the app shows the friendly Reload card, not a blank page', () => {
  jest.spyOn(console, 'error').mockImplementation(() => {});
  window.history.pushState({}, '', '/chat');
  render(<App />);
  expect(screen.getByTestId('error-boundary')).toBeInTheDocument();
  expect(screen.getByRole('alert')).toHaveTextContent(/Something went wrong/i);
  expect(screen.getByRole('button', { name: 'Reload' })).toBeInTheDocument();
  expect(screen.queryByText(/layout exploded/)).not.toBeInTheDocument();
  console.error.mockRestore();
});
