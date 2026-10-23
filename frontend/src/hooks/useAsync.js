import { useCallback, useEffect, useRef, useState } from 'react';
import { friendlyError } from '../utils/friendlyError';

/** Becomes true once `active` has stayed true for `afterMs` (for "still working…" copy). */
export function useSlowFlag(active, afterMs = 5000) {
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    if (!active) {
      setSlow(false);
      return undefined;
    }
    const t = setTimeout(() => setSlow(true), afterMs);
    return () => clearTimeout(t);
  }, [active, afterMs]);
  return slow;
}

/**
 * Shared async-state pattern: idle -> loading -> success | error.
 *
 *   const { status, data, error, run, retry, isLoading, isSlow } =
 *     useAsync(() => apiClient.get('/api/x').then(r => r.data), { immediate: true });
 *
 * - `status` is 'loading' for the whole request, including apiClient's own retries,
 *   so the UI shows a loader (never an error) while the backend is slow or waking up.
 * - `error` is friendly copy (see utils/friendlyError); `rawError` keeps the original.
 * - `retry()` re-runs the last call with the same arguments.
 * - Results from a stale call (superseded or unmounted) are ignored.
 */
export function useAsync(asyncFn, { immediate = false, slowAfterMs = 5000, errorFallback } = {}) {
  const [state, setState] = useState({
    status: immediate ? 'loading' : 'idle',
    data: undefined,
    error: null,
    rawError: null,
  });
  const fnRef = useRef(asyncFn);
  fnRef.current = asyncFn;
  const lastArgs = useRef([]);
  const callId = useRef(0);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const run = useCallback(async (...args) => {
    lastArgs.current = args;
    const id = ++callId.current;
    setState((s) => ({ ...s, status: 'loading', error: null, rawError: null }));
    try {
      const data = await fnRef.current(...args);
      if (mounted.current && id === callId.current) {
        setState({ status: 'success', data, error: null, rawError: null });
      }
      return data;
    } catch (err) {
      if (mounted.current && id === callId.current) {
        console.error('Request failed:', err);
        setState((s) => ({ ...s, status: 'error', error: friendlyError(err, errorFallback), rawError: err }));
      }
      return undefined;
    }
  }, [errorFallback]);

  const retry = useCallback(() => run(...lastArgs.current), [run]);
  const reset = useCallback(() => {
    callId.current += 1;
    setState({ status: 'idle', data: undefined, error: null, rawError: null });
  }, []);

  useEffect(() => {
    if (immediate) run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [immediate]);

  const isLoading = state.status === 'loading';
  const isSlow = useSlowFlag(isLoading, slowAfterMs);

  return { ...state, run, retry, reset, isLoading, isSlow };
}

export default useAsync;
