import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { ErrorState } from './AsyncState';

const defaultReload = () => {
  if (typeof window !== 'undefined' && window.location) window.location.reload();
};

/**
 * Catches render errors below it and shows the friendly ErrorState card with a
 * Reload button instead of a blank page. Raw error text is never shown to users;
 * pass `showDetails` (dev only) to expose the component stack.
 *
 * `resetKey`: when it changes (e.g. the active tab), the boundary clears itself,
 * so moving to another tab recovers without a full reload.
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    console.error('Uncaught UI error:', error, errorInfo);
    if (this.props.onError) this.props.onError(error, errorInfo);
  }

  componentDidUpdate(prevProps) {
    if (this.state.hasError && prevProps.resetKey !== this.props.resetKey) {
      this.resetErrorBoundary();
    }
  }

  resetErrorBoundary = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) this.props.onReset();
  };

  render() {
    if (!this.state.hasError) return this.props.children;

    const { title, message, onReload, showDetails, className } = this.props;
    return (
      <div className={`pp-error-boundary ${className || ''}`} data-testid="error-boundary">
        <ErrorState
          title={title}
          message={message}
          onRetry={onReload || defaultReload}
          retryLabel="Reload"
        />
        {showDetails && this.state.errorInfo && (
          <details className="pp-error-boundary__details">
            <summary>Technical details</summary>
            <pre>{String(this.state.error)}{this.state.errorInfo.componentStack}</pre>
          </details>
        )}
      </div>
    );
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node,
  title: PropTypes.string,
  message: PropTypes.string,
  onReload: PropTypes.func,
  onReset: PropTypes.func,
  onError: PropTypes.func,
  resetKey: PropTypes.any,
  showDetails: PropTypes.bool,
  className: PropTypes.string,
};

ErrorBoundary.defaultProps = {
  title: 'Something went wrong',
  message: 'This page hit an unexpected problem. Reloading usually fixes it.',
  showDetails: false,
};

export default ErrorBoundary;
