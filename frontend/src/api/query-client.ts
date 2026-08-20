import { QueryClient } from '@tanstack/react-query';

export function isCancelledQueryError(
  error: unknown,
): boolean {
  if (!error || typeof error !== 'object') {
    return false;
  }

  const candidate = error as {
    name?: string;
    code?: string;
  };

  return (
    candidate.name === 'CanceledError'
    || candidate.name === 'AbortError'
    || candidate.code === 'ERR_CANCELED'
  );
}

export function shouldRetryQuery(
  failureCount: number,
  error: unknown,
): boolean {
  if (isCancelledQueryError(error)) {
    return false;
  }

  return failureCount < 1;
}

export function createAppQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000,
        gcTime: 30 * 60 * 1000,
        refetchOnWindowFocus: false,
        retry: shouldRetryQuery,
      },
    },
  });
}

export const appQueryClient =
  createAppQueryClient();
