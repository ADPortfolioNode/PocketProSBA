import React from 'react';
import { Link } from 'react-router-dom';

/**
 * Slim brand strip — logo only. Primary nav lives in SBANavigation.
 */
function Header() {
  return (
    <header className="pp-brand-bar" role="banner">
      <div className="pp-shell pp-brand-inner">
        <Link to="/" className="pp-logo" aria-label="PocketPro SBA home">
          <span className="pp-logo-mark" aria-hidden="true" />
          <span className="pp-logo-text">
            PocketPro <span className="pp-logo-muted">SBA</span>
          </span>
        </Link>
      </div>
    </header>
  );
}

export default Header;
