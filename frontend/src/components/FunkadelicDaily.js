import React, { useState } from 'react';
import {
  FUNKADELIC,
  REHEARSAL_ROOMS,
  SOLO_DUO_RATES,
  RECORDING,
  POLICIES,
  roomRate,
  bookingQuote,
} from '../data/funkadelicDaily';
import './FunkadelicDaily.css';

const TABS = ['Rooms', 'Recording', 'Repair', 'Rentals & Retail', 'Events', 'Expansion'];

function FunkadelicDaily() {
  const [tab, setTab] = useState('Rooms');
  const [roomId, setRoomId] = useState(3);
  const [period, setPeriod] = useState('day');
  const [hours, setHours] = useState(2);
  const [payByCard, setPayByCard] = useState(true);
  const [largeGroup, setLargeGroup] = useState(false);
  const [bookings, setBookings] = useState([]);
  const [bookingName, setBookingName] = useState('');
  const [repairItem, setRepairItem] = useState('');
  const [repairIssue, setRepairIssue] = useState('');
  const [repairs, setRepairs] = useState([]);

  const room = REHEARSAL_ROOMS.find((r) => r.id === roomId) || REHEARSAL_ROOMS[0];
  const rate = roomRate(room, period, largeGroup);
  const quote = bookingQuote({ rate, hours, payByCard });

  const addBooking = (e) => {
    e.preventDefault();
    if (!bookingName.trim()) return;
    setBookings((b) => [
      ...b,
      {
        name: bookingName.trim(),
        room: room.name,
        period,
        hours,
        total: quote.total,
        deposit: quote.deposit,
      },
    ]);
    setBookingName('');
  };

  const addRepair = (e) => {
    e.preventDefault();
    if (!repairItem.trim()) return;
    setRepairs((r) => [...r, { item: repairItem.trim(), issue: repairIssue.trim() }]);
    setRepairItem('');
    setRepairIssue('');
  };

  return (
    <div className="funkadelic-daily">
      <header className="funkadelic-header">
        <p className="funkadelic-kicker">CUSTOM DEPLOY PROTOTYPE — EXISTING BUSINESS</p>
        <h1>{FUNKADELIC.name}</h1>
        <p>{FUNKADELIC.description}</p>
        <p>
          {FUNKADELIC.address} · {FUNKADELIC.hours} · {FUNKADELIC.phone}
        </p>
        <p className="funkadelic-note">
          Demo only: this prototype takes no payments and makes no real reservations.
          Verify rates and policies with the studio before booking. SBA guidance here
          is not a loan approval — a lender and the SBA decide eligibility, amount,
          and timing.
        </p>
      </header>

      <div className="funkadelic-tabs" role="tablist" aria-label="Daily business functions">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            role="tab"
            aria-selected={tab === t}
            className={tab === t ? 'is-active' : ''}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === 'Rooms' && (
        <section>
          <h2>Rehearsal rooms — daily bookings</h2>
          <p>Ten rooms, day (11am–6pm) and evening (6pm–11pm) rates. Existing-business use first: regular bookings, not startup setup.</p>
          <label>
            Room
            <select value={roomId} onChange={(e) => setRoomId(Number(e.target.value))}>
              {REHEARSAL_ROOMS.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name} — up to {r.capacity} people
                </option>
              ))}
            </select>
          </label>
          <label>
            Time
            <select value={period} onChange={(e) => setPeriod(e.target.value)}>
              <option value="day">Day (11am–6pm)</option>
              <option value="evening">Evening (6pm–11pm)</option>
            </select>
          </label>
          <label>
            Hours
            <input type="number" min="1" max="12" value={hours} onChange={(e) => setHours(Number(e.target.value) || 1)} />
          </label>
          {room.id === 1 && (
            <label>
              <input type="checkbox" checked={largeGroup} onChange={(e) => setLargeGroup(e.target.checked)} />
              {' '}13–20 people (Studio 1 large-group rate)
            </label>
          )}
          <label>
            <input type="checkbox" checked={payByCard} onChange={(e) => setPayByCard(e.target.checked)} />
            {' '}Pay by card (4% processing fee; cash has no fee)
          </label>
          <p className="funkadelic-quote">
            Rate: ${rate}/hr · Base: ${quote.base} · Fee: ${quote.fee} · Total: ${quote.total} · Deposit due (50%): ${quote.deposit}
          </p>
          <form onSubmit={addBooking}>
            <label>
              Booking name
              <input value={bookingName} onChange={(e) => setBookingName(e.target.value)} placeholder="Band / artist name" />
            </label>
            <button type="submit">Add demo booking</button>
          </form>
          <ul>
            {bookings.map((b, i) => (
              <li key={i}>
                {b.name} — {b.room}, {b.period}, {b.hours}h — total ${b.total}, deposit ${b.deposit}
              </li>
            ))}
          </ul>
          <h3>Solo / duo / teacher rates</h3>
          <ul>
            {SOLO_DUO_RATES.map((r) => (
              <li key={r.label}>{r.label}: ${r.day}/hr day, ${r.evening}/hr evening</li>
            ))}
          </ul>
          <p>{POLICIES.cancellation}</p>
          <p>{POLICIES.soloEveningNote}</p>
        </section>
      )}

      {tab === 'Recording' && (
        <section>
          <h2>Recording studio</h2>
          <p>${RECORDING.hourlyRange}/hour. Vocal sessions: {RECORDING.vocalMinimum}; instrumental sessions: {RECORDING.instrumentalMinimum}. Production ${RECORDING.productionRange}/hour. {RECORDING.cancellation}; {RECORDING.depositPercent}% deposit. {RECORDING.note}</p>
          <p>Daily function: book a recording session, confirm engineer availability, and keep the session file with the booking.</p>
        </section>
      )}

      {tab === 'Repair' && (
        <section>
          <h2>Repair shop</h2>
          <p>Free estimate on every job. Amps, speakers, guitars, basses, keys, and more — the shop described as the most affordable in NYC.</p>
          <form onSubmit={addRepair}>
            <label>
              Instrument / gear
              <input value={repairItem} onChange={(e) => setRepairItem(e.target.value)} placeholder="e.g. Fender amp" />
            </label>
            <label>
              Issue
              <input value={repairIssue} onChange={(e) => setRepairIssue(e.target.value)} placeholder="e.g. no sound on channel 2" />
            </label>
            <button type="submit">Add repair intake (demo)</button>
          </form>
          <ul>
            {repairs.map((r, i) => (
              <li key={i}>{r.item} — {r.issue || 'estimate requested'}</li>
            ))}
          </ul>
        </section>
      )}

      {tab === 'Rentals & Retail' && (
        <section>
          <h2>Rentals &amp; retail</h2>
          <p>Daily functions: rent backline gear (Marshall, Fender, Yamaha, Roland, Ampeg, Shure, and more), and sell retail gear and accessories to musicians using the rooms.</p>
          <ul>
            <li>Gear rental check-out / check-in</li>
            <li>Retail sales to rehearsal customers</li>
            <li>Damage / maintenance log for rented gear</li>
          </ul>
        </section>
      )}

      {tab === 'Events' && (
        <section>
          <h2>Events &amp; community</h2>
          <ul>
            <li>Saturday night Open Jam</li>
            <li>Drum Club</li>
            <li>Beginner band showcases</li>
            <li>Off-Broadway musical theatre rehearsal support</li>
            <li>Rock &amp; roll club nights</li>
          </ul>
          <p>These are existing-business community functions, not a new-business launch plan.</p>
        </section>
      )}

      {tab === 'Expansion' && (
        <section>
          <h2>Expansion — prepared scope, only if asked</h2>
          <p>
            <strong>Do not assume expansion is wanted.</strong> This section is prepared
            so the demo can answer it immediately if Funkadelic asks, and stays
            unused otherwise.
          </p>
          <h3>If asked, the expansion scope to discuss</h3>
          <ul>
            <li>Second rehearsal room / additional floor space, and soundproofing upgrades</li>
            <li>Additional backline and recording equipment</li>
            <li>Staffing for extended hours, recording, and repair</li>
            <li>Lease, build-out, and equipment quotes to support any financing discussion</li>
          </ul>
          <h3>SBA options to show (guidance only, broad net)</h3>
          <ul>
            <li>7(a) — working capital, equipment, and general business purposes</li>
            <li>504 — major fixed assets such as real estate and large equipment</li>
            <li>Working capital / line of credit for seasonal cash flow</li>
          </ul>
          <p>
            Expectation note: this is guidance only, not a loan approval or eligibility
            decision. A lender and the SBA decide eligibility, amount, and timing, and
            will ask for financials, tax returns, lease, and quotes.
          </p>
          <a href="/chat">Ask the concierge about expansion →</a>
        </section>
      )}
    </div>
  );
}

export default FunkadelicDaily;
