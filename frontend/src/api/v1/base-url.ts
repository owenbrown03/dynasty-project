const DEFAULT_DEV_API_BASE_URL =
  'http://localhost:8000/api/v1';

export function resolveApiBaseUrl(
  locationOrigin?: string,
): string {
  const isLocalhost =
    locationOrigin
    && /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/i.test(
      locationOrigin,
    );

  return isLocalhost
    ? DEFAULT_DEV_API_BASE_URL
    : '/api/v1';
}