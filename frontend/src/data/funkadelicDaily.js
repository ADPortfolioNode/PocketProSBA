// Funkadelic Studios, NYC — daily business functions (custom deploy prototype).
// Public information only, from funkadelicstudios.com (rates / about pages)
// as researched 2026-10-25. Verify rates and policies with the studio before
// using this for real bookings — this prototype takes no payments and makes
// no real reservations. See the expectation note in FunkadelicDaily.js.

export const FUNKADELIC = {
  name: 'Funkadelic Studios',
  address: '209 W 40th St, 5th Fl, New York, NY 10018',
  phone: '+1 212-696-2513',
  website: 'https://www.funkadelicstudios.com/',
  hours: 'Daily, 11:00 AM – 11:00 PM',
  description:
    'Established NYC rehearsal and recording studio in Times Square, in business for over 25 years. Ten rehearsal rooms, a recording studio, a repair shop, rentals, a retail shop, and a rock & roll club — the “six Rs”.',
};

// Hourly rehearsal rates: [day 11am–6pm, evening 6pm–11pm].
// Band rooms: Studio 1 day/evening rate is for 12 people or fewer;
// 13–20 people is $65 day / $75 evening.
export const REHEARSAL_ROOMS = [
  { id: 1, name: 'Studio 1', capacity: 20, day: 60, evening: 70, dayLarge: 65, eveningLarge: 75 },
  { id: 2, name: 'Studio 2', capacity: 5, day: 35, evening: 45 },
  { id: 3, name: 'Studio 3', capacity: 8, day: 40, evening: 50 },
  { id: 4, name: 'Studio 4', capacity: 3, day: 30, evening: 40 },
  { id: 5, name: 'Studio 5', capacity: 3, day: 30, evening: 40 },
  { id: 6, name: 'Studio 6', capacity: 5, day: 35, evening: 45 },
  { id: 7, name: 'Studio 7', capacity: 8, day: 40, evening: 50 },
  { id: 8, name: 'Studio 8', capacity: 8, day: 40, evening: 50 },
  { id: 9, name: 'Studio 9', capacity: 5, day: 35, evening: 45 },
  { id: 10, name: 'Studio 10', capacity: 10, day: 55, evening: 65 },
];

export const SOLO_DUO_RATES = [
  { label: 'Solo', day: 15, evening: 20 },
  { label: 'Duo', day: 30, evening: 40 },
  { label: 'Teacher', day: 20, evening: 35 },
];

export const RECORDING = {
  // Corrected 2026-10-25 from the studio's current recording page:
  // the old $50/hr was the videography basic rate, not recording.
  // No ten-hour block is listed on that page, so none is shown.
  hourlyRange: '80–100',
  vocalMinimum: '2-hour minimum',
  instrumentalMinimum: '3-hour minimum',
  productionRange: '100–125',
  depositPercent: 50,
  cancellation: '5-day cancellation policy',
  note: 'Recording includes a professional sound engineer.',
};

export const POLICIES = {
  depositPercent: 50,
  processingFeePercent: 4,
  cancellation:
    'Studios 1 & 10 require 5 days notice for a refund; Studios 2–9 require 2 days notice. A minimum 50% deposit is required for all bookings; bookings inside the cancellation window require full payment at booking. A 4% processing fee applies except for cash payments.',
  soloEveningNote:
    'Solo bookings for 6–11pm must be made on the same day. Call after 11am.',
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
