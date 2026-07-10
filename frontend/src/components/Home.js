import React from 'react';
import { Link } from 'react-router-dom';

const prompts = [
  { label: 'Loans', text: 'Which SBA loan fits a retail startup?' },
  { label: 'Apply', text: 'How do I prepare for a 7(a) application?' },
  { label: 'Compare', text: 'Compare 7(a) and 504 at a glance.' },
  { label: 'Eligibility', text: 'What are the basic SBA eligibility rules?' },
];

function Home() {
  return (
    <main className="pp-home">
      <section className="pp-hero">
        <p className="pp-eyebrow">SBA workspace</p>
        <h1 className="pp-hero-title">Clear guidance for small business funding.</h1>
        <p className="pp-hero-lead">
          Chat, browse resources, and run RAG workflows in one calm interface.
        </p>
        <div className="pp-hero-actions">
          <Link to="/chat" className="pp-btn pp-btn-primary">
            Start chat
          </Link>
          <Link to="/browse" className="pp-btn pp-btn-ghost">
            Browse resources
          </Link>
        </div>
      </section>

      <section className="pp-prompt-grid" aria-label="Suggested prompts">
        {prompts.map((item) => (
          <Link
            key={item.label}
            to="/chat"
            className="pp-prompt-card"
            state={{ draft: item.text }}
          >
            <span className="pp-prompt-label">{item.label}</span>
            <span className="pp-prompt-text">{item.text}</span>
          </Link>
        ))}
      </section>

      <section className="pp-feature-row" aria-label="Workspace areas">
        <div className="pp-feature">
          <h2>Chat</h2>
          <p>Ask concierge-style questions about SBA programs and next steps.</p>
        </div>
        <div className="pp-feature">
          <h2>RAG</h2>
          <p>Query the local knowledge base when live embeddings are offline.</p>
        </div>
        <div className="pp-feature">
          <h2>Tasks</h2>
          <p>Submit orchestration jobs with soft fallbacks for reliability.</p>
        </div>
      </section>
    </main>
  );
}

export default Home;
