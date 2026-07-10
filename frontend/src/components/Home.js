import React from 'react';
import { Link } from 'react-router-dom';

/** Live real-world photos (Unsplash) — service-app hero & feature cards */
const IMG = {
  hero:
    'https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&w=1400&q=80',
  chat:
    'https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?auto=format&fit=crop&w=800&q=80',
  browse:
    'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=800&q=80',
  rag:
    'https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=800&q=80',
  tasks:
    'https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=800&q=80',
  loans:
    'https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=800&q=80',
  storefront:
    'https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=800&q=80',
};

const prompts = [
  {
    label: 'Loans',
    text: 'Which SBA loan fits a retail startup?',
    image: IMG.loans,
  },
  {
    label: 'Apply',
    text: 'How do I prepare for a 7(a) application?',
    image: IMG.browse,
  },
  {
    label: 'Compare',
    text: 'Compare 7(a) and 504 at a glance.',
    image: IMG.rag,
  },
  {
    label: 'Eligibility',
    text: 'What are the basic SBA eligibility rules?',
    image: IMG.storefront,
  },
];

const services = [
  {
    to: '/chat',
    title: 'Concierge chat',
    blurb: 'Ask about programs, eligibility, and next steps in plain language.',
    image: IMG.chat,
  },
  {
    to: '/browse',
    title: 'Browse SBA content',
    blurb: 'Live loan guides and official sba.gov resources, kept current.',
    image: IMG.browse,
  },
  {
    to: '/rag',
    title: 'Knowledge RAG',
    blurb: 'Search the local knowledge base when you need offline depth.',
    image: IMG.rag,
  },
  {
    to: '/orchestrator',
    title: 'Task workflows',
    blurb: 'Break complex funding questions into guided steps.',
    image: IMG.tasks,
  },
];

function Home() {
  return (
    <main className="pp-home svc-home">
      <section className="svc-hero">
        <div className="svc-hero-copy">
          <p className="pp-eyebrow svc-eyebrow">SBA service workspace</p>
          <h1 className="pp-hero-title">Funding guidance built for small business.</h1>
          <p className="pp-hero-lead">
            A clean service experience for SBA loans, resources, and chat — white-glove clarity
            with live official content.
          </p>
          <div className="pp-hero-actions">
            <Link to="/chat" className="pp-btn pp-btn-primary">
              Start chat
            </Link>
            <Link to="/browse" className="pp-btn pp-btn-ghost">
              Browse resources
            </Link>
          </div>
        </div>
        <div className="svc-hero-media">
          <img
            src={IMG.hero}
            alt="Small business team collaborating in a modern office"
            className="svc-hero-img"
            loading="eager"
          />
          <div className="svc-hero-glow" aria-hidden="true" />
        </div>
      </section>

      <section className="svc-section" aria-label="Services">
        <div className="svc-section-head">
          <h2>Services</h2>
          <p>Everything you need in one calm, blue-and-white workspace.</p>
        </div>
        <div className="svc-service-grid">
          {services.map((s) => (
            <Link key={s.to} to={s.to} className="svc-service-card">
              <div className="svc-service-img-wrap">
                <img src={s.image} alt="" className="svc-service-img" loading="lazy" />
              </div>
              <div className="svc-service-body">
                <h3>{s.title}</h3>
                <p>{s.blurb}</p>
                <span className="svc-link">Open →</span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="svc-section" aria-label="Suggested prompts">
        <div className="svc-section-head">
          <h2>Popular questions</h2>
          <p>Jump straight into chat with a real-world scenario.</p>
        </div>
        <div className="pp-prompt-grid svc-prompt-grid">
          {prompts.map((item) => (
            <Link
              key={item.label}
              to="/chat"
              className="pp-prompt-card svc-prompt-card"
              state={{ draft: item.text }}
            >
              <div className="svc-prompt-thumb">
                <img src={item.image} alt="" loading="lazy" />
              </div>
              <div>
                <span className="pp-prompt-label">{item.label}</span>
                <span className="pp-prompt-text">{item.text}</span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="svc-band" aria-label="Live SBA content">
        <div className="svc-band-inner">
          <div>
            <h2>Current SBA loan programs</h2>
            <p>
              Browse pulls live text from official sba.gov pages so what you read matches the real
              world — not stale offline copy.
            </p>
            <Link to="/browse" className="pp-btn pp-btn-primary">
              View live loans
            </Link>
          </div>
          <img
            src={IMG.loans}
            alt="Business owner reviewing finances"
            className="svc-band-img"
            loading="lazy"
          />
        </div>
      </section>
    </main>
  );
}

export default Home;
