import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useSession } from '../hooks/useSession';
import { clearSession } from '../utils/authStorage';

/**
 * Sitewide brand mark: original rotating yin-yang animation.
 * Canonical file: /images/yinyang.gif (also served as /logo.gif)
 */
export const LOGO_SRC = `${process.env.PUBLIC_URL || ''}/images/yinyang.gif`;
export const LOGO_FALLBACK = `${process.env.PUBLIC_URL || ''}/logo.gif`;

/**
 * Slim brand strip — animated yin-yang logo + wordmark.
 * Primary nav lives in SBANavigation.
 */
function Header() {
  const { authenticated, user } = useSession();
  const navigate = useNavigate();
  const handleLogout = () => {
    clearSession();
    navigate('/', { replace: true });
  };
  const who = user?.name || user?.email;

  return (
    <header className="pp-brand-bar svc-brand" role="banner">
      <div className="pp-shell pp-brand-inner">
        <Link to="/" className="pp-logo" aria-label="PocketPro SBA home">
          <img
            className="pp-logo-img pp-logo-animated"
            src={LOGO_SRC}
            width="36"
            height="36"
            alt="PocketPro SBA"
            decoding="async"
            onError={(e) => {
              if (e.currentTarget.src.indexOf('logo.gif') === -1) {
                e.currentTarget.src = LOGO_FALLBACK;
              }
            }}
          />
          <span className="pp-logo-text">
            PocketPro <span className="pp-logo-muted">SBA</span>
          </span>
        </Link>
        <div className="pp-header-actions">
          <span className="svc-brand-tag d-none d-md-inline">Small business funding service</span>
          {authenticated ? (
            <>
              {who && (
                <span className="pp-header-user d-none d-sm-inline" title={user?.email || ''}>
                  {who}
                </span>
              )}
              <button type="button" className="btn btn-sm btn-outline-primary pp-header-auth" onClick={handleLogout}>
                Log out
              </button>
            </>
          ) : (
            <Link to="/login" className="btn btn-sm btn-outline-primary pp-header-auth">
              Log in
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}

export default Header;
