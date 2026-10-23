/**
 * Turn any thrown request error into short, human copy for the UI.
 * Raw exception text never reaches the screen; it stays in the console.
 *
 *  - 4xx with a short backend message (e.g. "Invalid credentials") -> that message
 *  - 5xx / gateway errors                                             -> generic "on our side"
 *  - no response (network down, refused, CORS)                        -> "couldn't reach"
 *  - timeout                                                          -> "taking longer than expected"
 */
export const ERROR_COPY = {
  network: "We couldn't reach PocketPro. Check your connection and try again.",
  timeout: 'This is taking longer than expected. Please try again.',
  server: 'Something went wrong on our side. Please try again in a moment.',
  generic: 'Something went wrong. Please try again.',
};

const looksTechnical = (msg) =>
  /exception|traceback|error:|errno|stack|undefined|null|\bat\s+\S+\s+\(|status code \d{3}|\w+Error\b/i.test(msg);

export function friendlyError(err, fallback = ERROR_COPY.generic) {
  if (!err) return fallback;
  if (typeof err === 'string') return looksTechnical(err) ? fallback : err;

  const status = err.response?.status;
  const body = err.response?.data;
  const backendMsg = typeof body === 'string' ? '' : (body?.error || body?.message || '');

  if (err.code === 'ECONNABORTED' || err.code === 'ETIMEDOUT' || /timeout/i.test(err.message || '')) {
    return ERROR_COPY.timeout;
  }
  if (status && status >= 400 && status < 500) {
    if (backendMsg && backendMsg.length <= 160 && !looksTechnical(backendMsg)) return backendMsg;
    return fallback;
  }
  if (status && status >= 500) return ERROR_COPY.server;
  if (!status && (err.request || err.code || /network/i.test(err.message || ''))) return ERROR_COPY.network;
  return fallback;
}

export default friendlyError;
