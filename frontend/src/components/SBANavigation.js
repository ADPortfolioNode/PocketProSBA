import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import PropTypes from 'prop-types';
import ConnectionStatusIndicator from './ConnectionStatusIndicator';
import { useScrollFade } from '../hooks/useScrollFade';

/**
 * Primary app nav.
 * Resources uses a full page load to /browse so nginx serves the live
 * resources.html UI (API nav + click-to-load + detail cards), not the
 * stale prebuilt CRA bundle's client-side route.
 */
export const NAV_ITEMS = [
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
    // Full page → programs.html (API cards + detail modal on click)
    hardNav: true,
  },
  { to: '/orchestrator', label: 'Tasks', testId: 'nav-orchestrator' },
  // Custom deploy prototype: Funkadelic Studios daily business functions.
  { to: '/daily', label: 'Daily', testId: 'nav-daily' },
];

const SBANavigation = ({ serverConnected, connectionStatus, apiUrl }) => {
  const location = useLocation();
  const currentPath = location.pathname.toLowerCase();
  // On narrow screens the links scroll sideways; fade the edge that has more.
  const { ref: scrollRef, fadeLeft, fadeRight } = useScrollFade();
  const navClass = `pp-nav${fadeLeft ? ' pp-nav--fade-left' : ''}${fadeRight ? ' pp-nav--fade-right' : ''}`;

  return (
    <nav className={navClass} aria-label="Primary" data-testid="primary-nav">
      <div className="pp-shell pp-nav-inner" ref={scrollRef}>
        <div className="pp-nav-links">
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
          <ConnectionStatusIndicator connected={serverConnected} status={connectionStatus} apiUrl={apiUrl} />
        </div>
      </div>
    </nav>
  );
};

SBANavigation.propTypes = {
  serverConnected: PropTypes.bool.isRequired,
  connectionStatus: PropTypes.oneOf(['checking', 'online', 'offline']),
  apiUrl: PropTypes.oneOfType([PropTypes.func, PropTypes.string]),
};

export default SBANavigation;
