import { describe, expect, it } from 'vitest';

import { resolveApiBaseUrl } from '@/api/v1/base-url';

describe('resolveApiBaseUrl', () => {
  it('uses the configured api base url when provided', () => {
    expect(
      resolveApiBaseUrl(
        'https://api.example.com/api/v1/',
      ),
    ).toBe('https://api.example.com/api/v1');
  });

  it('defaults to the local api container during localhost development', () => {
    expect(
      resolveApiBaseUrl(
        undefined,
        'http://localhost:5173',
      ),
    ).toBe('http://localhost:8000/api/v1');
  });

  it('defaults to a relative api path outside localhost development', () => {
    expect(
      resolveApiBaseUrl(
        undefined,
        'https://dynastybase.app',
      ),
    ).toBe('/api/v1');
  });
});
