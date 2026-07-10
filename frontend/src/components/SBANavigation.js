import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import PropTypes from 'prop-types';
import ConnectionStatusIndicator from './ConnectionStatusIndicator';

/**
 * Primary app nav.
 * Resources uses a full page load to /browse so nginx serves the live
 * resources.html UI (API nav + click-to-load + detail cards), not the
 * stale prebuilt CRA bundle's client-side route.
 */
const NAV_ITEMS = [
  { to: '/', label: 'Home', testId: 'nav-home', exact: true },
  { to: '/chat', label: 'Chat', testId: 'nav-chat' },
  {
    to: '/browse',
    label: 'Resources',
    testId: 'nav-browse',
    // Full document navigation → resources.html via nginx (API cards)
    hardNav: true,
  },
  { to: '/rag', label: 'RAG', testId: 'nav-rag' },
  { to: '/documents', label: 'Docs', testId: 'nav-documents' },
  {
    to: '/sba',
    label: 'Programs',
    testId: 'nav-sba',
    // SPA SBAContent: Programs | Lifecycle | Local from /api/sba/resources
  },
  { to: '/orchestrator', label: 'Tasks', testId: 'nav-orchestrator' },
];

const SBANavigation = ({ serverConnected, apiUrl }) => {
  const location = useLocation();
  const currentPath = location.pathname.toLowerCase();

  return (
    <nav className="pp-nav" aria-label="Primary">
      <div className="pp-shell pp-nav-inner">
        <div className="pp-nav-links" role="list">
          {NAV_ITEMS.map((item) => {
            const active = item.exact
              ? currentPath === '/' || currentPath === ''
              : currentPath === item.to ||
                currentPath.startsWith(`${item.to}/`) ||
                (item.to === '/browse' &&
                  (currentPath === '/resources' || currentPath === '/browse'));

            const className = `pp-nav-link${active ? ' is-active' : ''}`;
            const common = {
              className,
              'data-testid': item.testId,
              role: 'listitem',
              'aria-current': active ? 'page' : undefined,
            };

            if (item.hardNav) {
              return (
                <a key={item.to} href={item.to} {...common}>
                  {item.label}
                </a>
              );
            }

            return (
              <Link key={item.to} to={item.to} {...common}>
                {item.label}
              </Link>
            );
          })}
        </div>
        <div className="pp-nav-status">
          <ConnectionStatusIndicator connected={serverConnected} apiUrl={apiUrl} />
        </div>
      </div>
    </nav>
  );
};

SBANavigation.propTypes = {
  serverConnected: PropTypes.bool.isRequired,
  apiUrl: PropTypes.oneOfType([PropTypes.func, PropTypes.string]),
};

export default SBANavigation;
