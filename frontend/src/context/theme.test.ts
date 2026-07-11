import { describe, expect, it, vi } from 'vitest';

import {
  applyResolvedTheme,
  getStoredThemePreference,
  isThemePreference,
  resolveThemePreference,
  THEME_STORAGE_KEY,
} from '@/context/theme';

describe('theme utilities', () => {
  it('validates supported theme preferences', () => {
    expect(isThemePreference('light')).toBe(true);
    expect(isThemePreference('dark')).toBe(true);
    expect(isThemePreference('system')).toBe(true);
    expect(isThemePreference('sepia')).toBe(false);
  });

  it('reads a valid stored preference', () => {
    window.localStorage.setItem(
      THEME_STORAGE_KEY,
      'dark',
    );

    expect(getStoredThemePreference()).toBe('dark');
  });

  it('falls back to system for invalid stored values', () => {
    window.localStorage.setItem(
      THEME_STORAGE_KEY,
      'sepia',
    );

    expect(getStoredThemePreference()).toBe('system');
  });

  it('resolves system preference from matchMedia', () => {
    const matchMedia = vi.fn().mockReturnValue({
      matches: true,
    });

    vi.stubGlobal('matchMedia', matchMedia);

    expect(resolveThemePreference('system')).toBe('dark');
    expect(resolveThemePreference('light')).toBe('light');
  });

  it('applies the resolved theme to the document root', () => {
    const matchMedia = vi.fn().mockReturnValue({
      matches: false,
    });

    vi.stubGlobal('matchMedia', matchMedia);

    expect(applyResolvedTheme('system')).toBe('light');
    expect(
      document.documentElement.dataset.theme,
    ).toBe('light');
    expect(
      document.documentElement.style.colorScheme,
    ).toBe('light');
  });
});
