import type { AccentColor, ThemePreference } from '@/types';

export type ResolvedTheme = 'light' | 'dark';

export const THEME_STORAGE_KEY =
  'dynasty-theme-preference';

export const ACCENT_STORAGE_KEY =
  'dynasty-accent-color';

export const VALID_ACCENT_COLORS: AccentColor[] = [
  'blue', 'green', 'purple', 'red', 'orange', 'teal', 'pink',
];

export function isAccentColor(
  value: string | null,
): value is AccentColor {
  return VALID_ACCENT_COLORS.includes(
    value as AccentColor,
  );
}

export function getStoredAccentColor(): AccentColor {
  if (typeof window === 'undefined') {
    return 'blue';
  }

  const stored = window.localStorage.getItem(
    ACCENT_STORAGE_KEY,
  );

  if (isAccentColor(stored)) {
    return stored;
  }

  return 'blue';
}

export function applyAccentColor(
  accent: AccentColor,
): void {
  if (accent === 'blue') {
    delete document.documentElement.dataset.accent;
  } else {
    document.documentElement.dataset.accent = accent;
  }
}

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
