import React from 'react';
import PropTypes from 'prop-types';
import LoadingBar from './LoadingBar';
import '../styles/loading.css';

/** Friendly failure card with a Retry button. Shown only after a real failure. */
export function ErrorState({
  title = "That didn't load",
  message = 'Something went wrong. Please try again.',
  onRetry,
  retryLabel = 'Retry',
  compact = false,
  className,
}) {
  return (
    <div className={`pp-error-state ${compact ? 'is-compact' : ''} ${className || ''}`} role="alert" data-testid="error-state">
      <div className="pp-error-state__icon" aria-hidden="true">!</div>
      <div className="pp-error-state__body">
        {title && <p className="pp-error-state__title">{title}</p>}
        <p className="pp-error-state__msg">{message}</p>
        {onRetry && (
          <button type="button" className="pp-btn pp-btn-primary pp-error-state__retry" onClick={onRetry}>
            {retryLabel}
          </button>
        )}
      </div>
    </div>
  );
}

ErrorState.propTypes = {
  title: PropTypes.string,
  message: PropTypes.string,
  onRetry: PropTypes.func,
  retryLabel: PropTypes.string,
  compact: PropTypes.bool,
  className: PropTypes.string,
};


/**
 * Render the right thing for an async status from useAsync():
 * loading -> candy-stripe bar, error -> ErrorState with Retry, otherwise children.
 */
export function AsyncContent({ status, error, onRetry, loadingLabel, slow, errorTitle, children }) {
  if (status === 'loading') return <LoadingBar label={loadingLabel} slow={slow} />;
  if (status === 'error') return <ErrorState title={errorTitle} message={error || undefined} onRetry={onRetry} />;
  return <>{children}</>;
}

AsyncContent.propTypes = {
  status: PropTypes.oneOf(['idle', 'loading', 'success', 'error']).isRequired,
  error: PropTypes.string,
  onRetry: PropTypes.func,
  loadingLabel: PropTypes.string,
  slow: PropTypes.bool,
  errorTitle: PropTypes.string,
  children: PropTypes.node,
};

export default AsyncContent;
