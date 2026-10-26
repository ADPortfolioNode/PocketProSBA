// Daily operations for a service business — generic, no client branding.
// Example rates below are placeholders: a business replaces them with its
// own rates, rooms, and policies. This is a demo workflow only: it takes
// no payments and makes no real reservations. Verify rates and policies
// with the business before using it for real bookings.

export const OPERATING_HOURS = {
  openHour: 11,
  closeHour: 23,
  label: 'Daily, 11:00 AM – 11:00 PM',
};

// Bookable rooms, priced per hour. Day = 11am–6pm, evening = 6pm–11pm.
// Room 1's large-group rate applies to groups of 13–20 people.
export const BOOKABLE_ROOMS = [
  { id: 1, name: 'Room 1', capacity: 20, day: 60, evening: 70, dayLarge: 65, eveningLarge: 75 },
  { id: 2, name: 'Room 2', capacity: 5, day: 35, evening: 45 },
  { id: 3, name: 'Room 3', capacity: 8, day: 40, evening: 50 },
  { id: 4, name: 'Room 4', capacity: 3, day: 30, evening: 40 },
  { id: 5, name: 'Room 5', capacity: 3, day: 30, evening: 40 },
  { id: 6, name: 'Room 6', capacity: 5, day: 35, evening: 45 },
  { id: 7, name: 'Room 7', capacity: 8, day: 40, evening: 50 },
  { id: 8, name: 'Room 8', capacity: 8, day: 40, evening: 50 },
  { id: 9, name: 'Room 9', capacity: 5, day: 35, evening: 45 },
  { id: 10, name: 'Room 10', capacity: 10, day: 55, evening: 65 },
];

export const INDIVIDUAL_RATES = [
  { label: 'Solo', day: 15, evening: 20 },
  { label: 'Duo', day: 30, evening: 40 },
  { label: 'Teacher', day: 20, evening: 35 },
];

export const RECORDING = {
  hourlyRange: '80–100',
  vocalMinimum: '2-hour minimum',
  instrumentalMinimum: '3-hour minimum',
  productionRange: '100–125',
  depositPercent: 50,
  cancellation: '5-day cancellation policy',
  fullPayment:
    'Bookings made within 5 days of the session require full payment at the time of booking.',
  filesStored: 'Session files are stored for 6 months unless instructed otherwise.',
  bookingVia:
    'For a real session, send project details on the booking form and wait for the studio to reply with availability.',
  note: 'Recording includes a professional sound engineer.',
};

// Cancellation, deposit, and booking terms, following the business's own
// published rehearsal and recording terms (rooms numbered 1–10, as here):
// Rooms 1 and 10 need 5 days' notice to cancel for a refund, Rooms 2–9 need
// 2 days' notice; cancelling within 48 hours or not showing up charges the
// full booking cost; a $25 fee applies when a drumset must be removed from
// a room; solo evening bookings are same-day only, call after 11am.
export const POLICIES = {
  depositPercent: 50,
  processingFeePercent: 4,
  cancellation:
    'Cancellation: Rooms 1 and 10 require 5 days’ notice to cancel for a refund; Rooms 2–9 require 2 days’ notice. Cancelling within 48 hours, or not showing up, charges the full booking cost. A $25 fee applies to any room rental requiring removal of the drumset.',
  deposit:
    'A minimum 50% deposit is required for all bookings. Bookings made inside the cancellation policy require full payment at the time of booking. For Rooms 2–9, bookings costing $100 or more require a $50 deposit at the time of booking. A 4% processing fee applies except for cash payments.',
  soloEvening:
    'Solo evening bookings (6–11pm) must be made on the same day. Call after 11am.',
};

export function roomRate(room, period, largeGroup = false) {
  if (period === 'evening') {
    return largeGroup && room.eveningLarge ? room.eveningLarge : room.evening;
  }
  return largeGroup && room.dayLarge ? room.dayLarge : room.day;
}

export function bookingQuote({ rate, hours, payByCard = true }) {
  const base = rate * hours;
  const fee = payByCard ? Math.round(base * (POLICIES.processingFeePercent / 100) * 100) / 100 : 0;
  const total = Math.round((base + fee) * 100) / 100;
  const deposit = Math.round((total * POLICIES.depositPercent) / 100 * 100) / 100;
  return { base, fee, total, deposit };
}

// --- Calendar scheduling, down to the room and the hour ---

export function formatHour(hour) {
  const h = hour % 24;
  const suffix = h < 12 ? 'am' : 'pm';
  const display = h % 12 === 0 ? 12 : h % 12;
  return `${display}${suffix}`;
}

// Hourly start slots that leave at least one hour before close.
export function hourlyStartSlots() {
  const slots = [];
  for (let h = OPERATING_HOURS.openHour; h < OPERATING_HOURS.closeHour; h += 1) {
    slots.push(h);
  }
  return slots;
}

export function isWithinOperatingHours(startHour, durationHours) {
  if (!Number.isFinite(startHour) || !Number.isFinite(durationHours) || durationHours < 1) {
    return false;
  }
  return (
    startHour >= OPERATING_HOURS.openHour &&
    startHour + durationHours <= OPERATING_HOURS.closeHour
  );
}

// Bookings are { date: 'YYYY-MM-DD', service: string, startHour, endHour }.
// Two bookings conflict only for the same service on the same date with
// overlapping hours; back-to-back bookings (end === start) do not conflict.
export function hasConflict(bookings, candidate) {
  return bookings.some(
    (b) =>
      b.date === candidate.date &&
      b.service === candidate.service &&
      candidate.startHour < b.endHour &&
      candidate.endHour > b.startHour,
  );
}
