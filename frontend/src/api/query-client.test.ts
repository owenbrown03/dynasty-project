import { describe, expect, it } from 'vitest';

import {
  isCancelledQueryError,
  shouldRetryQuery,
} from './query-client';


describe('query client retry policy', () => {
  it('treats axios and abort cancellations as cancelled', () => {
    expect(
      isCancelledQueryError({
        name: 'CanceledError',
        code: 'ERR_CANCELED',
      }),
    ).toBe(true);
    expect(
      isCancelledQueryError({
        name: 'AbortError',
      }),
    ).toBe(true);
    expect(
      isCancelledQueryError({
        name: 'Error',
        code: 'ERR_NETWORK',
      }),
    ).toBe(false);
  });

  it('does not retry cancelled queries', () => {
    expect(
      shouldRetryQuery(0, {
        name: 'CanceledError',
        code: 'ERR_CANCELED',
      }),
    ).toBe(false);
  });

  it('retries a real failure once', () => {
    expect(
      shouldRetryQuery(0, {
        name: 'Error',
      }),
    ).toBe(true);
    expect(
      shouldRetryQuery(1, {
        name: 'Error',
      }),
    ).toBe(false);
  });
});
