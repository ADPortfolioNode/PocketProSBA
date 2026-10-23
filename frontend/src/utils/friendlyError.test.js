import { friendlyError, ERROR_COPY } from './friendlyError';

describe('friendlyError', () => {
  test('keeps short backend messages for 4xx (e.g. bad credentials)', () => {
    expect(friendlyError({ response: { status: 401, data: { error: 'Invalid credentials' } } })).toBe('Invalid credentials');
  });

  test('hides technical 4xx/5xx bodies and raw axios text', () => {
    expect(friendlyError({ response: { status: 500, data: { error: 'Failed to process message: KeyError: x' } } })).toBe(ERROR_COPY.server);
    expect(friendlyError({ response: { status: 400, data: { error: 'TypeError: undefined is not a function' } } })).toBe(ERROR_COPY.generic);
    expect(friendlyError({ message: 'Request failed with status code 502', response: { status: 502 } })).toBe(ERROR_COPY.server);
  });

  test('maps network failures and timeouts', () => {
    expect(friendlyError(Object.assign(new Error('Network Error'), { code: 'ERR_NETWORK', request: {} }))).toBe(ERROR_COPY.network);
    expect(friendlyError({ code: 'ECONNABORTED', message: 'timeout of 60000ms exceeded' })).toBe(ERROR_COPY.timeout);
  });

  test('uses the caller fallback for unknown errors', () => {
    expect(friendlyError(new Error('boom'), 'Upload failed.')).toBe('Upload failed.');
    expect(friendlyError(null, 'x')).toBe('x');
  });
});
