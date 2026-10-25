import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import FunkadelicDaily from './FunkadelicDaily';
import { bookingQuote, roomRate, REHEARSAL_ROOMS } from '../data/funkadelicDaily';

describe('FunkadelicDaily', () => {
  test('renders existing-business daily functions, not a startup plan', () => {
    render(<FunkadelicDaily />);
    expect(screen.getByText('Funkadelic Studios')).toBeInTheDocument();
    expect(screen.getByText(/Rehearsal rooms/)).toBeInTheDocument();
    expect(screen.getByText(/Demo only/)).toBeInTheDocument();
  });

  test('room quote includes deposit and card fee', () => {
    const room = REHEARSAL_ROOMS.find((r) => r.id === 3);
    expect(roomRate(room, 'day')).toBe(40);
    const quote = bookingQuote({ rate: 40, hours: 2, payByCard: true });
    expect(quote.base).toBe(80);
    expect(quote.total).toBe(83.2);
    expect(quote.deposit).toBe(41.6);
  });

  test('expansion is a prepared scope tab, not the default', () => {
    render(<FunkadelicDaily />);
    expect(screen.getByRole('tab', { name: /expansion/i })).toBeInTheDocument();
    expect(screen.queryByText(/Do not assume expansion/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('tab', { name: /expansion/i }));
    expect(screen.getByText(/Do not assume expansion/)).toBeInTheDocument();
    expect(screen.getByText(/prepared scope, only if asked/i)).toBeInTheDocument();
  });
});
