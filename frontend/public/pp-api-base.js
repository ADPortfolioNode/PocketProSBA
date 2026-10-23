/* PocketPro static pages (/browse, /sba): where the API lives.
 *
 * Same origin by default, so nginx/the dev proxy serves /api. A deployment that
 * hosts the API elsewhere sets REACT_APP_API_URL (or REACT_APP_BACKEND_URL) at
 * build time; scripts/inject-api-base.js writes it into the
 * <meta name="pp-api-base"> tag of each static page, the same value the React
 * app's apiClient uses. There is deliberately no 127.0.0.1/localhost fallback:
 * it only ever worked on a developer machine.
 */
(function (root) {
  function normalize(base) {
    return String(base || '').trim().replace(/\/api\/?$/, '').replace(/\/+$/, '');
  }

  function ppApiBase(doc, loc) {
    doc = doc || root.document;
    loc = loc || root.location;
    var meta = doc && doc.querySelector ? doc.querySelector('meta[name="pp-api-base"]') : null;
    var configured = meta ? meta.getAttribute('content') : '';
    // An unreplaced %REACT_APP_API_URL% placeholder (dev server, plain copy) means "not configured".
    if (configured && configured.indexOf('%') === -1 && /^https?:\/\//i.test(configured.trim())) {
      return normalize(configured);
    }
    return loc.origin;
  }

  /** Absolute URL for an API path (e.g. "/api/sba/resources"). */
  function ppApiUrl(path, doc, loc) {
    return new URL(path, ppApiBase(doc, loc) + '/').toString();
  }

  root.ppApiBase = ppApiBase;
  root.ppApiUrl = ppApiUrl;
})(typeof window !== 'undefined' ? window : this);
