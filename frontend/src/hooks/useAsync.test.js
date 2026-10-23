import { renderHook, act, waitFor } from '@testing-library/react';
import { useAsync, useSlowFlag } from './useAsync';

describe('useAsync', () => {
  beforeEach(() => jest.spyOn(console, 'error').mockImplementation(() => {}));
  afterEach(() => console.error.mockRestore());

  test('immediate: starts in loading (never error) and resolves to success', async () => {
    let resolve;
    const fn = jest.fn(() => new Promise((r) => { resolve = r; }));
    const { result } = renderHook(() => useAsync(fn, { immediate: true }));

    expect(result.current.status).toBe('loading');
    expect(result.current.error).toBeNull();

    await act(async () => { resolve({ ok: 1 }); });
    expect(result.current.status).toBe('success');
    expect(result.current.data).toEqual({ ok: 1 });
  });

  test('failure gives friendly copy, and retry re-runs with the same args', async () => {
    const fn = jest.fn()
      .mockRejectedValueOnce({ response: { status: 503 } })
      .mockResolvedValueOnce('second time lucky');
    const { result } = renderHook(() => useAsync(fn));

    await act(async () => { await result.current.run('a', 1); });
    expect(result.current.status).toBe('error');
    expect(result.current.error).toMatch(/on our side/i);
    expect(result.current.error).not.toMatch(/503|status code/);

    await act(async () => { await result.current.retry(); });
    expect(fn).toHaveBeenLastCalledWith('a', 1);
    expect(result.current.status).toBe('success');
    expect(result.current.data).toBe('second time lucky');
  });

  test('ignores a stale call that resolves after a newer one', async () => {
    const resolvers = [];
    const fn = jest.fn(() => new Promise((r) => resolvers.push(r)));
    const { result } = renderHook(() => useAsync(fn));

    act(() => { result.current.run(1); });
    act(() => { result.current.run(2); });
    await act(async () => { resolvers[1]('new'); });
    await act(async () => { resolvers[0]('old'); });
    expect(result.current.data).toBe('new');
  });
});

describe('useSlowFlag', () => {
  test('turns on after the delay while active, resets when inactive', () => {
    jest.useFakeTimers();
    const { result, rerender } = renderHook(({ on }) => useSlowFlag(on, 1000), { initialProps: { on: true } });
    expect(result.current).toBe(false);
    act(() => { jest.advanceTimersByTime(1000); });
    expect(result.current).toBe(true);
    rerender({ on: false });
    expect(result.current).toBe(false);
    jest.useRealTimers();
  });
});
