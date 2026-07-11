import type { ThemePreference } from '@/types';

export type ResolvedTheme = 'light' | 'dark';

export const THEME_STORAGE_KEY =
  'dynasty-theme-preference';

export function isThemePreference(
  value: string | null,
): value is ThemePreference {
  return value === 'light'
    || value === 'dark'
    || value === 'system';
}

export function getStoredThemePreference(): ThemePreference {
  if (typeof window === 'undefined') {
    return 'system';
  }

  const stored = window.localStorage.getItem(
    THEME_STORAGE_KEY,
  );

  if (isThemePreference(stored)) {
    return stored;
  }

  return 'system';
}

export function resolveThemePreference(
  preference: ThemePreference,
): ResolvedTheme {
  if (preference === 'light' || preference === 'dark') {
    return preference;
  }

  if (
    typeof window !== 'undefined'
    && window.matchMedia(
      '(prefers-color-scheme: dark)',
    ).matches
  ) {
    return 'dark';
  }

  return 'light';
}

export function applyResolvedTheme(
  preference: ThemePreference,
): ResolvedTheme {
  const resolved = resolveThemePreference(
    preference,
  );

  document.documentElement.dataset.theme = resolved;
  document.documentElement.style.colorScheme = resolved;

  return resolved;
}
