import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import PropTypes from 'prop-types';
import ConnectionStatusIndicator from './ConnectionStatusIndicator';

const NAV_ITEMS = [
  { to: '/', label: 'Home', testId: 'nav-home', exact: true },
  { to: '/chat', label: 'Chat', testId: 'nav-chat' },
  { to: '/browse', label: 'Resources', testId: 'nav-browse' },
  { to: '/rag', label: 'RAG', testId: 'nav-rag' },
  { to: '/documents', label: 'Docs', testId: 'nav-documents' },
  { to: '/sba', label: 'SBA', testId: 'nav-sba' },
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
              : currentPath === item.to || currentPath.startsWith(`${item.to}/`);
            return (
              <Link
                key={item.to}
                to={item.to}
                role="listitem"
                data-testid={item.testId}
                className={`pp-nav-link${active ? ' is-active' : ''}`}
                aria-current={active ? 'page' : undefined}
              >
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
