import '@testing-library/jest-dom';

// jsdom does not implement scrollIntoView (used by chat auto-scroll)
if (typeof window !== 'undefined' && window.HTMLElement && !window.HTMLElement.prototype.scrollIntoView) {
  window.HTMLElement.prototype.scrollIntoView = function scrollIntoView() {};
}
