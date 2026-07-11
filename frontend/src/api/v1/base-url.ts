const DEFAULT_DEV_API_BASE_URL =
  'http://localhost:8000/api/v1';

function trimTrailingSlash(
  value: string,
): string {
  return value.replace(/\/+$/, '');
}

export function resolveApiBaseUrl(
  configuredBaseUrl?: string,
  locationOrigin?: string,
): string {
  const normalizedConfiguredBaseUrl =
    configuredBaseUrl?.trim();

  if (normalizedConfiguredBaseUrl) {
    return trimTrailingSlash(
      normalizedConfiguredBaseUrl,
    );
  }

  if (
    locationOrigin
    && /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/i.test(
      locationOrigin,
    )
  ) {
    return DEFAULT_DEV_API_BASE_URL;
  }

  return '/api/v1';
}
