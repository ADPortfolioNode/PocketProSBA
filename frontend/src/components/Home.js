import React from 'react';
import { Link } from 'react-router-dom';

const useCases = [
  {
    title: 'Smart Loan Planning',
    description: 'Personalize SBA loan guidance, compare terms, and identify optimal funding paths for small business growth.',
    image: 'https://images.unsplash.com/photo-1551033406-611cf9d37654?auto=format&fit=crop&w=900&q=80',
    alt: 'Business planning meeting',
  },
  {
    title: 'Grant & Funding Insights',
    description: 'Discover SBA grants and disaster relief options tailored to your industry and operational needs.',
    image: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=900&q=80',
    alt: 'Business finance dashboard',
  },
  {
    title: 'Fast Approval Roadmap',
    description: 'Prepare documentation, track readiness, and reduce approval time with guided SBA workflows.',
    image: 'https://images.unsplash.com/photo-1542223616-8835eda33251?auto=format&fit=crop&w=900&q=80',
    alt: 'Portrait of business owner',
  },
];

function Home() {
  return (
    <main className="home-hero page-home">
      <section className="home-hero-banner container py-5">
        <div className="row align-items-center gy-4">
          <div className="col-lg-6">
            <span className="badge bg-info text-dark mb-3">SBA Assistant</span>
            <h1 className="display-5 fw-bold">Simplified SBA guidance for small business success.</h1>
            <p className="lead text-muted">
              Track current SBA program status, explore real-world use cases, and get intelligent funding recommendations in one streamlined workspace.
            </p>
            <div className="home-hero-actions d-flex flex-wrap gap-3 mt-4">
              <Link to="/chat" className="btn btn-primary btn-lg">Start SBA Chat</Link>
              <Link to="/" className="btn btn-outline-primary btn-lg">Browse Use Cases</Link>
            </div>
          </div>
          <div className="col-lg-6">
            <div className="home-hero-visual shadow-lg rounded-4 overflow-hidden">
              <img
                src="https://images.unsplash.com/photo-1515378791036-0648a3ef77b2?auto=format&fit=crop&w=1200&q=80"
                alt="SBA assistant dashboard"
                className="img-fluid home-hero-image"
                loading="eager"
              />
            </div>
          </div>
        </div>
      </section>

      <section className="home-status container pb-5">
        <div className="row g-4">
          <div className="col-md-4">
            <div className="status-card p-4 rounded-4 h-100">
              <h5>Current SBA Status</h5>
              <p className="text-muted">Live snapshot of SBA program availability and trending support areas.</p>
              <ul className="status-list list-unstyled mt-4">
                <li><strong>Open applications:</strong> 12,400+</li>
                <li><strong>Approval rate:</strong> 86% for SBA 7(a)</li>
                <li><strong>Top sector:</strong> Technology & services</li>
              </ul>
            </div>
          </div>
          <div className="col-md-8">
            <div className="suggestion-panel p-4 rounded-4 h-100">
              <div className="d-flex justify-content-between align-items-start mb-3">
                <div>
                  <span className="badge bg-white text-dark">Use Case Suggestions</span>
                  <h4 className="mt-3">Get started with the most valuable SBA scenarios</h4>
                </div>
                <div className="text-end text-muted">
                  <small>Updated daily • Photorealistic insights</small>
                </div>
              </div>
              <div className="row g-3">
                {useCases.map((useCase, index) => (
                  <div key={index} className="col-sm-6 col-xl-4">
                    <div className="use-case-card rounded-4 overflow-hidden h-100 shadow-sm">
                      <img src={useCase.image} alt={useCase.alt} className="img-fluid" loading="lazy" />
                      <div className="p-3 bg-dark text-white">
                        <h6 className="mb-2">{useCase.title}</h6>
                        <p className="small text-white-75 mb-0">{useCase.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}

export default Home;
