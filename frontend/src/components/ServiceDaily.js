import React, { useState } from 'react';
import {
  OPERATING_HOURS,
  BOOKABLE_ROOMS,
  INDIVIDUAL_RATES,
  RECORDING,
  POLICIES,
  roomRate,
  bookingQuote,
  formatHour,
  hourlyStartSlots,
  isWithinOperatingHours,
  hasConflict,
} from '../data/serviceDaily';
import './ServiceDaily.css';

const TABS = ['Rooms', 'Recording', 'Repair', 'Rentals & Retail', 'Events', 'Growth'];

// Logo as published on funkadelicstudios.com (Squarespace CDN, purple wordmark
// with white 30 anniversary mark, designed to sit on a dark banner).
const LOGO_URL =
  'https://images.squarespace-cdn.com/content/v1/58fa6ab446c3c493b8941bae/f980aa3c-fb6b-4c09-b54f-1c166f95be5e/Funk30logo+purple+white.png?format=1500w';
const today = () => new Date().toISOString().slice(0, 10);

// One card per task. A tab is a service area; a card is the actual job a
// person does in that area — what it does, the steps, what you need, and
// what you get. Cards marked "Workflow outline" describe a job that has no
// working form on this page yet, so the page never pretends a list is a
// working workflow.
const WORKFLOW_CARDS = {
  Rooms: [
    {
      title: 'Check availability',
      what: 'See which hours are free for one room on one date.',
      steps: ['Pick a room and a date.', 'Read the day schedule, hour by hour: Free or Booked.', 'Pick a free start time for the quote and booking cards.'],
      needs: 'Room and date',
      result: 'A free start time inside operating hours.',
    },
    {
      title: 'Get a quote',
      what: 'Price a session before anyone commits to it.',
      steps: ['Pick the room, day or evening rate, and number of hours.', 'Choose card or cash — card adds the 4% processing fee.', 'Read the quote: base, fee, total, and 50% deposit due.', 'Check the cancellation terms for the room: Rooms 1 and 10 need 5 days’ notice, Rooms 2–9 need 2 days’ notice.'],
      needs: 'Room, time of day, and hours',
      result: 'A quoted total and deposit, with nothing booked yet.',
    },
    {
      title: 'Add a demo booking',
      what: 'Hold a room for a session in this demo.',
      steps: ['Add a booking name, date, start time, and hours.', 'The page blocks it if the room is already booked for part of that time.', 'The page blocks it if it starts or ends outside operating hours.'],
      needs: 'Booking name, date, start time, and hours',
      result: 'The booking appears in the day schedule and the bookings list.',
      target: 'rooms-booking-form',
    },
  ],
  Recording: [
    {
      title: 'Book a recording session',
      what: 'Hold the recording studio for a session in this demo.',
      steps: ['Pick a date, start time, and hours inside operating hours.', 'Add a session name.', 'The page blocks it if the studio is already booked for part of that time.', 'For a real session, send project details on the booking form and wait for the studio to reply with availability.'],
      needs: 'Date, start time, hours, and session name',
      result: 'The session appears in the recording bookings list.',
      target: 'recording-booking-form',
    },
    {
      title: 'Confirm engineer and deposit',
      what: 'Turn a held session into a confirmed booking with the studio.',
      steps: ['Confirm engineer availability with the studio.', 'Confirm the session minimum: vocal 2 hours, instrumental 3 hours.', 'Take the 50% deposit; the 5-day recording cancellation policy applies.', 'Bookings made within 5 days of the session require full payment at the time of booking.'],
      needs: 'Engineer availability and the deposit',
      result: 'A confirmed session, with its file stored for 6 months unless instructed otherwise.',
      status: 'Confirm with the studio — this step is not a form on this page',
    },
  ],
  Repair: [
    {
      title: 'Open a repair intake',
      what: 'Log a broken item so the shop can look at it.',
      steps: ['Add the instrument or gear.', 'Describe the issue.', 'Submit the intake.'],
      needs: 'Item, and the issue if known',
      result: 'The intake appears in the repair list, with a free estimate requested.',
      target: 'repair-intake-form',
    },
    {
      title: 'Get a free estimate',
      what: 'Find out what the repair will cost before any work starts.',
      steps: ['The shop reviews the intake.', 'The shop gives an estimate.', 'The customer approves it before work begins.'],
      needs: 'An open intake',
      result: 'An approved estimate — no work starts without one.',
      status: 'Workflow outline — the estimate step is handled by the shop, not a form here',
    },
  ],
  'Rentals & Retail': [
    {
      title: 'Rent gear',
      what: 'Lend backline gear to a customer using the rooms.',
      steps: ['Check the gear out to the customer.', 'Check it back in when it returns.', 'Log any damage or maintenance it needs.'],
      needs: 'Gear item and customer',
      result: 'Gear tracked from check-out to check-in, with damage logged.',
      status: 'Workflow outline — no form yet',
    },
    {
      title: 'Sell retail',
      what: 'Sell gear and accessories to customers using the services.',
      steps: ['Pick the retail item.', 'Record the sale to the service customer.', 'Update stock.'],
      needs: 'Retail item and customer',
      result: 'A recorded retail sale.',
      status: 'Workflow outline — no form yet',
    },
  ],
  Events: [
    {
      title: 'Run a community event',
      what: 'Put on an event in the space, such as an Open Jam, Drum Club, or showcase.',
      steps: ['Pick the event type.', 'Book the space for it on the Rooms tab.', 'Promote it to the community.'],
      needs: 'Event type and a booked space',
      result: 'An event with space held for it.',
      actionTab: 'Rooms',
    },
    {
      title: 'Support a theatre rehearsal',
      what: 'Host a musical theatre rehearsal as a service customer.',
      steps: ['Book the room for the rehearsal block.', 'Confirm the schedule with the company.', 'Keep the booking in the day schedule.'],
      needs: 'Company, room, and rehearsal dates',
      result: 'A rehearsal block held in the schedule.',
      actionTab: 'Rooms',
    },
  ],
  Growth: [
    {
      title: 'Discuss growth scope — only if asked',
      what: 'Talk through more space, equipment, or staffing, only when the business asks for it.',
      steps: ['Ask whether growth is wanted at all.', 'Walk the prepared scope: space, soundproofing, equipment, staffing.', 'Gather lease, build-out, and equipment quotes.'],
      needs: 'The business asking for it',
      result: 'A scoped growth discussion, with quotes to support any financing talk.',
    },
    {
      title: 'Explore SBA options',
      what: 'Show financing guidance for an existing business, without promising an outcome.',
      steps: ['Ask the concierge about the growth scope.', 'Compare 7(a), 504, and working-capital guidance.', 'Note what a lender will ask for: financials, tax returns, lease, and quotes.'],
      needs: 'A growth scope to discuss',
      result: 'Guidance only — not a loan approval or eligibility decision.',
    },
  ],
};

// How each tab's cards relate to each other. 'sequence' tabs are one
// workflow executed in order (do step 1, then step 2); 'choice' tabs hold
// separate workflows — pick the one you need, they are not steps of each
// other. This distinction is shown in the UI so the order is never guessed.
const WORKFLOW_MODE = {
  Rooms: 'sequence',
  Recording: 'sequence',
  Repair: 'sequence',
  'Rentals & Retail': 'choice',
  Events: 'choice',
  Growth: 'sequence',
};

const WORKFLOW_DEFINITIONS = {
  Rooms: 'Take a room from a free hour to a held booking.',
  Recording: 'Take a recording session from a hold to a confirmed booking.',
  Repair: 'Take a broken item from intake to an approved estimate.',
  'Rentals & Retail': 'Lend gear or sell retail to a service customer.',
  Events: 'Put on an event in the space, or host a rehearsal block.',
  Growth: 'Talk growth through only when the business asks for it, then show financing guidance.',
};

function WorkflowCards({ tab, setTab }) {
  const cards = WORKFLOW_CARDS[tab] || [];
  const mode = WORKFLOW_MODE[tab] || 'sequence';
  const isSequence = mode === 'sequence';
  const unit = isSequence ? 'Step' : 'Workflow';
  return (
    <section className="service-workflows" aria-label={`Workflows in ${tab}`}>
      <h2>Workflows in {tab}</h2>
      <p>{WORKFLOW_DEFINITIONS[tab]}</p>
      <p>
        {isSequence
          ? 'Follow these steps in order — each step builds on the last:'
          : 'Pick the workflow you need — these are separate jobs, not steps of each other:'}
      </p>
      <ol className="service-workflow-sequence">
        {cards.map((card) => (
          <li key={card.title}>{card.title}</li>
        ))}
      </ol>
      <div className="service-task-grid">
        {cards.map((card, index) => {
          const isLast = index === cards.length - 1;
          const next = !isLast ? cards[index + 1] : null;
          return (
            <article key={card.title} className="service-task-card">
              <p className="service-task-number">
                {unit} {index + 1} of {cards.length}
              </p>
              <h3>{card.title}</h3>
              {card.status && <p className="service-task-status">{card.status}</p>}
              <p>{card.what}</p>
              <ol aria-label="Steps in order">
                {card.steps.map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ol>
              <p>
                <strong>Needs:</strong> {card.needs}
              </p>
              <p>
                <strong>Result:</strong> {card.result}
              </p>
              {card.target && (
                <a href={`#${card.target}`}>
                  Do {unit.toLowerCase()} {index + 1} →
                </a>
              )}
              {card.actionTab && (
                <button type="button" onClick={() => setTab(card.actionTab)}>
                  Go to {card.actionTab} →
                </button>
              )}
              {isSequence && next && (
                <p className="service-task-next">
                  Next: {unit} {index + 2} — {next.title}
                </p>
              )}
              {isSequence && isLast && (
                <p className="service-task-next">Workflow complete.</p>
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}

function ServiceDaily() {
  const [tab, setTab] = useState('Rooms');
  const [roomId, setRoomId] = useState(3);
  const [period, setPeriod] = useState('day');
  const [hours, setHours] = useState(2);
  const [payByCard, setPayByCard] = useState(true);
  const [largeGroup, setLargeGroup] = useState(false);
  const [bookings, setBookings] = useState([]);
  const [bookingName, setBookingName] = useState('');
  const [bookingDate, setBookingDate] = useState(today());
  const [startHour, setStartHour] = useState(14);
  const [scheduleError, setScheduleError] = useState('');
  const [recordingDate, setRecordingDate] = useState(today());
  const [recordingStart, setRecordingStart] = useState(14);
  const [recordingHours, setRecordingHours] = useState(2);
  const [recordingName, setRecordingName] = useState('');
  const [repairItem, setRepairItem] = useState('');
  const [repairIssue, setRepairIssue] = useState('');
  const [repairs, setRepairs] = useState([]);

  const room = BOOKABLE_ROOMS.find((r) => r.id === roomId) || BOOKABLE_ROOMS[0];
  const rate = roomRate(room, period, largeGroup);
  const quote = bookingQuote({ rate, hours, payByCard });
  const endHour = startHour + hours;
  const daySchedule = hourlyStartSlots().map((h) => {
    const booked = bookings.find(
      (b) => b.date === bookingDate && b.service === room.name && h >= b.startHour && h < b.endHour,
    );
    return { hour: h, booked: booked || null };
  });

  const addBooking = (e, service, date, start, duration, name, total, deposit) => {
    e.preventDefault();
    const candidate = { date, service, startHour: start, endHour: start + duration };
    if (!name.trim()) {
      setScheduleError('Add a booking name first.');
      return;
    }
    if (!isWithinOperatingHours(start, duration)) {
      setScheduleError(
        `Outside operating hours (${OPERATING_HOURS.label}). Bookings must start at or after ${formatHour(OPERATING_HOURS.openHour)} and end by ${formatHour(OPERATING_HOURS.closeHour)}.`,
      );
      return;
    }
    if (hasConflict(bookings, candidate)) {
      setScheduleError(`${service} is already booked for part of that time on ${date}. Pick another time.`);
      return;
    }
    setScheduleError('');
    setBookings((b) => [...b, { ...candidate, name: name.trim(), total, deposit }]);
  };

  const addRepair = (e) => {
    e.preventDefault();
    if (!repairItem.trim()) return;
    setRepairs((r) => [...r, { item: repairItem.trim(), issue: repairIssue.trim() }]);
    setRepairItem('');
    setRepairIssue('');
  };

  return (
    <div className="service-daily service-daily--branded">
      <header className="service-brand-header">
        <img src={LOGO_URL} alt="Funkadelic Studios logo" className="service-brand-logo" />
        <div className="service-brand-copy">
          <p className="service-kicker">FUNKADELIC STUDIOS · TIMES SQUARE, NYC</p>
          <h1>Daily operations</h1>
        <p>
          Calendar scheduling for the services a business offers, down to the room and
          the hour, within operating hours ({OPERATING_HOURS.label}). Example rates and
          rooms below are placeholders — replace them with your own.
        </p>
        <p className="service-note">
          Demo only: this workflow takes no payments and makes no real reservations.
          Verify rates and policies with the business before booking. SBA guidance here
          is not a loan approval — a lender and the SBA decide eligibility, amount,
          and timing.
        </p>
        </div>
        <p className="service-brand-hours">Open daily · 11am–11pm<br />(212) 696-2513</p>
      </header>

      <div className="service-layout">
        <nav className="service-sidebar" aria-label="Daily services">
          <div className="service-tabs" role="tablist" aria-label="Daily business functions">
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
        </nav>
        <div className="service-main">
          <WorkflowCards tab={tab} setTab={setTab} />

      {tab === 'Rooms' && (
        <section>
          <h2>Bookable rooms — calendar scheduling by the hour</h2>
          <p>Ten rooms, day (11am–6pm) and evening (6pm–11pm) rates. Pick a date and a start time inside operating hours; the schedule below shows what is already booked for that room that day.</p>
          <label>
            Room
            <select value={roomId} onChange={(e) => setRoomId(Number(e.target.value))}>
              {BOOKABLE_ROOMS.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name} — up to {r.capacity} people
                </option>
              ))}
            </select>
          </label>
          <label>
            Time of day (for the rate)
            <select value={period} onChange={(e) => setPeriod(e.target.value)}>
              <option value="day">Day (11am–6pm)</option>
              <option value="evening">Evening (6pm–11pm)</option>
            </select>
          </label>
          <label>
            Date
            <input type="date" value={bookingDate} onChange={(e) => setBookingDate(e.target.value)} />
          </label>
          <label>
            Start time
            <select value={startHour} onChange={(e) => setStartHour(Number(e.target.value))}>
              {hourlyStartSlots().map((h) => (
                <option key={h} value={h}>{formatHour(h)}</option>
              ))}
            </select>
          </label>
          <label>
            Hours
            <input type="number" min="1" max="12" value={hours} onChange={(e) => setHours(Number(e.target.value) || 1)} />
          </label>
          {room.id === 1 && (
            <label>
              <input type="checkbox" checked={largeGroup} onChange={(e) => setLargeGroup(e.target.checked)} />
              {' '}13–20 people (Room 1 large-group rate)
            </label>
          )}
          <label>
            <input type="checkbox" checked={payByCard} onChange={(e) => setPayByCard(e.target.checked)} />
            {' '}Pay by card (4% processing fee; cash has no fee)
          </label>
          <p className="service-quote">
            {formatHour(startHour)}–{formatHour(endHour)} · Rate: ${rate}/hr · Base: ${quote.base} · Fee: ${quote.fee} · Total: ${quote.total} · Deposit due (50%): ${quote.deposit}
          </p>
          {scheduleError && <p role="alert">{scheduleError}</p>}
          <form id="rooms-booking-form" onSubmit={(e) => addBooking(e, room.name, bookingDate, startHour, hours, bookingName, quote.total, quote.deposit)}>
            <label>
              Booking name
              <input value={bookingName} onChange={(e) => setBookingName(e.target.value)} placeholder="Band / artist name" />
            </label>
            <button type="submit">Add demo booking</button>
          </form>
          <h3>Day schedule — {room.name} on {bookingDate}</h3>
          <ul>
            {daySchedule.map((s) => (
              <li key={s.hour}>
                {formatHour(s.hour)}–{formatHour(s.hour + 1)}: {s.booked ? `Booked — ${s.booked.name}` : 'Free'}
              </li>
            ))}
          </ul>
          <h3>All demo bookings</h3>
          <ul>
            {bookings.map((b, i) => (
              <li key={i}>
                {b.name} — {b.service}, {b.date}, {formatHour(b.startHour)}–{formatHour(b.endHour)}
                {b.total ? ` — total $${b.total}, deposit $${b.deposit}` : ''}
              </li>
            ))}
          </ul>
          <h3>Solo / duo / teacher rates</h3>
          <ul>
            {INDIVIDUAL_RATES.map((r) => (
              <li key={r.label}>{r.label}: ${r.day}/hr day, ${r.evening}/hr evening</li>
            ))}
          </ul>
          <p>{POLICIES.cancellation}</p>
          <p>{POLICIES.deposit}</p>
          <p>{POLICIES.soloEvening}</p>
        </section>
      )}

      {tab === 'Recording' && (
        <section>
          <h2>Recording studio</h2>
          <p>${RECORDING.hourlyRange}/hour. Vocal sessions: {RECORDING.vocalMinimum}; instrumental sessions: {RECORDING.instrumentalMinimum}. Production ${RECORDING.productionRange}/hour. {RECORDING.cancellation}; {RECORDING.depositPercent}% deposit. {RECORDING.fullPayment} {RECORDING.filesStored} {RECORDING.note}</p>
          <p>Schedule a session inside operating hours, confirm engineer availability, and keep the session file with the booking.</p>
          {scheduleError && <p role="alert">{scheduleError}</p>}
          <form
            id="recording-booking-form"
            onSubmit={(e) => {
              addBooking(e, 'Recording studio', recordingDate, recordingStart, recordingHours, recordingName, null, null);
            }}
          >
            <label>
              Date
              <input type="date" value={recordingDate} onChange={(e) => setRecordingDate(e.target.value)} />
            </label>
            <label>
              Start time
              <select value={recordingStart} onChange={(e) => setRecordingStart(Number(e.target.value))}>
                {hourlyStartSlots().map((h) => (
                  <option key={h} value={h}>{formatHour(h)}</option>
                ))}
              </select>
            </label>
            <label>
              Hours
              <input type="number" min="1" max="12" value={recordingHours} onChange={(e) => setRecordingHours(Number(e.target.value) || 1)} />
            </label>
            <label>
              Booking name
              <input value={recordingName} onChange={(e) => setRecordingName(e.target.value)} placeholder="Artist / session name" />
            </label>
            <button type="submit">Add recording booking (demo)</button>
          </form>
          <ul>
            {bookings.filter((b) => b.service === 'Recording studio').map((b, i) => (
              <li key={i}>{b.name} — {b.date}, {formatHour(b.startHour)}–{formatHour(b.endHour)}</li>
            ))}
          </ul>
        </section>
      )}

      {tab === 'Repair' && (
        <section>
          <h2>Repair shop</h2>
          <p>Free estimate on every job. Amps, speakers, guitars, basses, keys, and more.</p>
          <form id="repair-intake-form" onSubmit={addRepair}>
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
          <p>Daily functions: rent backline gear, and sell retail gear and accessories to customers using the rooms.</p>
          <ul>
            <li>Gear rental check-out / check-in</li>
            <li>Retail sales to service customers</li>
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
            <li>Musical theatre rehearsal support</li>
            <li>Club nights</li>
          </ul>
          <p>These are existing-business community functions, not a new-business launch plan.</p>
        </section>
      )}

      {tab === 'Growth' && (
        <section>
          <h2>Growth — prepared scope, only if asked</h2>
          <p>
            <strong>Do not assume growth is wanted.</strong> This section is prepared
            so the demo can answer it immediately if asked, and stays
            unused otherwise.
          </p>
          <h3>If asked, the growth scope to discuss</h3>
          <ul>
            <li>Additional room / floor space, and soundproofing upgrades</li>
            <li>Additional equipment</li>
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
          <a href="/chat">Ask the concierge about growth →</a>
        </section>
      )}
        </div>
      </div>
    </div>
  );
}

export default ServiceDaily;
