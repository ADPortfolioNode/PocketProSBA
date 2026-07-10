import React from 'react';
import { Link } from 'react-router-dom';

/** Sitewide brand mark: yin-yang GIF */
export const LOGO_SRC = `${process.env.PUBLIC_URL || ''}/logo.gif`;
export const LOGO_FALLBACK = `${process.env.PUBLIC_URL || ''}/images/yinyang.gif`;

/**
 * Slim brand strip — yin-yang logo + wordmark.
 * Primary nav lives in SBANavigation.
 */
function Header() {
  return (
    <header className="pp-brand-bar svc-brand" role="banner">
      <div className="pp-shell pp-brand-inner">
        <Link to="/" className="pp-logo" aria-label="PocketPro SBA home">
          <img
            className="pp-logo-img"
            src={LOGO_SRC}
            width="36"
            height="36"
            alt="PocketPro SBA"
            decoding="async"
            onError={(e) => {
              if (e.currentTarget.src.indexOf('yinyang.gif') === -1) {
                e.currentTarget.src = LOGO_FALLBACK;
              }
            }}
          />
          <span className="pp-logo-text">
            PocketPro <span className="pp-logo-muted">SBA</span>
          </span>
        </Link>
        <span className="svc-brand-tag d-none d-md-inline">Small business funding service</span>
      </div>
    </header>
  );
}

export default Header;
