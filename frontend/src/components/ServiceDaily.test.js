import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ServiceDaily from './ServiceDaily';
import {
  bookingQuote,
  roomRate,
  BOOKABLE_ROOMS,
  isWithinOperatingHours,
  hasConflict,
  hourlyStartSlots,
} from '../data/serviceDaily';

describe('ServiceDaily', () => {
  test('renders generic daily operations with no client brand name', () => {
    const { container } = render(<ServiceDaily />);
    expect(screen.getByText('Daily operations')).toBeInTheDocument();
    expect(screen.getByText(/Bookable rooms/)).toBeInTheDocument();
    expect(screen.getByText(/Demo only/)).toBeInTheDocument();
    expect(container.textContent).not.toMatch(/Funkadelic/i);
  });

  test('room quote includes deposit and card fee', () => {
    const room = BOOKABLE_ROOMS.find((r) => r.id === 3);
    expect(roomRate(room, 'day')).toBe(40);
    const quote = bookingQuote({ rate: 40, hours: 2, payByCard: true });
    expect(quote.base).toBe(80);
    expect(quote.total).toBe(83.2);
    expect(quote.deposit).toBe(41.6);
  });

  test('growth is a prepared scope tab, not the default', () => {
    render(<ServiceDaily />);
    expect(screen.getByRole('tab', { name: /growth/i })).toBeInTheDocument();
    expect(screen.queryByText(/Do not assume growth/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('tab', { name: /growth/i }));
    expect(screen.getByText(/Do not assume growth/)).toBeInTheDocument();
    expect(screen.getByText(/prepared scope, only if asked/i)).toBeInTheDocument();
  });

  test('scheduling stays inside operating hours (11am–11pm)', () => {
    expect(hourlyStartSlots()[0]).toBe(11);
    expect(hourlyStartSlots().slice(-1)[0]).toBe(22);
    expect(isWithinOperatingHours(11, 1)).toBe(true);
    expect(isWithinOperatingHours(22, 1)).toBe(true);
    expect(isWithinOperatingHours(10, 1)).toBe(false);
    expect(isWithinOperatingHours(22, 2)).toBe(false);
    expect(isWithinOperatingHours(14, 0)).toBe(false);
  });

  test('conflicts are per service, date, and overlapping hour only', () => {
    const bookings = [{ date: '2026-10-26', service: 'Room 3', startHour: 14, endHour: 16 }];
    expect(hasConflict(bookings, { date: '2026-10-26', service: 'Room 3', startHour: 15, endHour: 17 })).toBe(true);
    expect(hasConflict(bookings, { date: '2026-10-26', service: 'Room 3', startHour: 16, endHour: 17 })).toBe(false);
    expect(hasConflict(bookings, { date: '2026-10-26', service: 'Room 4', startHour: 15, endHour: 17 })).toBe(false);
    expect(hasConflict(bookings, { date: '2026-10-27', service: 'Room 3', startHour: 15, endHour: 17 })).toBe(false);
  });

  test('adding a booking shows it in the day schedule and blocks a double booking', () => {
    render(<ServiceDaily />);
    const nameInput = screen.getByPlaceholderText('Band / artist name');
    fireEvent.change(nameInput, { target: { value: 'Test Band' } });
    fireEvent.click(screen.getByRole('button', { name: 'Add demo booking' }));
    expect(screen.getByText(/Test Band — Room 3/)).toBeInTheDocument();
    fireEvent.change(nameInput, { target: { value: 'Second Band' } });
    fireEvent.click(screen.getByRole('button', { name: 'Add demo booking' }));
    expect(screen.getByRole('alert')).toHaveTextContent(/already booked/);
    expect(screen.queryByText(/Second Band — Room 3/)).not.toBeInTheDocument();
  });
});
