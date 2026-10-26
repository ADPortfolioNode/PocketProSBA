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

  test('rooms tab shows one card per task with steps, needs, and result', () => {
    render(<ServiceDaily />);
    expect(screen.getByText('Workflows in Rooms — one card per task')).toBeInTheDocument();
    expect(screen.getByText('Check availability')).toBeInTheDocument();
    expect(screen.getByText('Get a quote')).toBeInTheDocument();
    expect(screen.getByText('Add a demo booking')).toBeInTheDocument();
    expect(screen.getByText(/A free start time inside operating hours/)).toBeInTheDocument();
    expect(screen.getByText(/A quoted total and deposit/)).toBeInTheDocument();
  });

  test('rooms tab states the published cancellation, deposit, and solo-evening terms', () => {
    render(<ServiceDaily />);
    expect(screen.getByText(/Rooms 1 and 10 require 5 days/)).toBeInTheDocument();
    expect(screen.getByText(/Rooms 2–9 require 2 days/)).toBeInTheDocument();
    expect(screen.getByText(/Solo evening bookings \(6–11pm\) must be made on the same day/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('tab', { name: /recording/i }));
    expect(screen.getAllByText(/Bookings made within 5 days of the session require full payment/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/stored for 6 months/).length).toBeGreaterThan(0);
  });

  test('repair tab shows its own task cards, and outline cards do not pretend to be forms', () => {
    render(<ServiceDaily />);
    fireEvent.click(screen.getByRole('tab', { name: /repair/i }));
    expect(screen.getByText('Workflows in Repair — one card per task')).toBeInTheDocument();
    expect(screen.getByText('Open a repair intake')).toBeInTheDocument();
    expect(screen.getByText(/Workflow outline/)).toBeInTheDocument();
    expect(screen.queryByText('Check availability')).not.toBeInTheDocument();
  });

  test('rentals tab cards are workflow outlines, not working booking forms', () => {
    render(<ServiceDaily />);
    fireEvent.click(screen.getByRole('tab', { name: /rentals/i }));
    expect(screen.getByText('Rent gear')).toBeInTheDocument();
    expect(screen.getByText('Sell retail')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Add demo booking' })).not.toBeInTheDocument();
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
