import '@testing-library/jest-dom';

// jsdom does not implement scrollIntoView (used by chat auto-scroll)
if (typeof window !== 'undefined' && window.HTMLElement && !window.HTMLElement.prototype.scrollIntoView) {
  window.HTMLElement.prototype.scrollIntoView = function scrollIntoView() {};
}

// apiClient retries transient failures with a ~15s back-off; keep the retries
// (so the policy is exercised) but make them instant in unit tests.
globalThis.__PP_RETRY_DELAY_MS__ = 0;
