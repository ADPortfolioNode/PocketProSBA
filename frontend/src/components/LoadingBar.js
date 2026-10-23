import React from 'react';
import PropTypes from 'prop-types';
import '../styles/loading.css';

/**
 * Candy-stripe indeterminate progress bar: the app's one loading indicator.
 * Use it wherever data is pending (startup, cold backend, retries).
 * `inline` renders the small pinwheel variant for tight spots (buttons, badges).
 */
function LoadingBar({
  label = 'Loading…',
  slowLabel = 'Still working — the service may be waking up. Hang tight…',
  slow = false,
  inline = false,
  className,
  'data-testid': testId,
}) {
  const text = slow && slowLabel ? slowLabel : label;
  if (inline) {
    return (
      <span className={`pp-pinwheel-wrap ${className || ''}`} role="status" aria-live="polite" data-testid={testId || 'loading-inline'}>
        <span className="pp-pinwheel" aria-hidden="true" />
        {text && <span className="pp-pinwheel-label">{text}</span>}
        {!text && <span className="visually-hidden">Loading</span>}
      </span>
    );
  }
  return (
    <div className={`pp-loading ${className || ''}`} role="status" aria-live="polite" data-testid={testId || 'loading-bar'}>
      <div
        className="pp-loading-bar"
        role="progressbar"
        aria-label={text || 'Loading'}
        aria-busy="true"
        aria-valuetext={text || 'Loading'}
      >
        <div className="pp-loading-bar__fill" />
      </div>
      {text && <p className="pp-loading-label">{text}</p>}
    </div>
  );
}

LoadingBar.propTypes = {
  label: PropTypes.string,
  slowLabel: PropTypes.string,
  slow: PropTypes.bool,
  inline: PropTypes.bool,
  className: PropTypes.string,
  'data-testid': PropTypes.string,
};


export default LoadingBar;
