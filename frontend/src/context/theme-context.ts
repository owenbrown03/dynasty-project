import { createContext } from 'react';

import type { AccentColor, ThemePreference } from '@/types';

type ResolvedTheme = 'light' | 'dark';

export type ThemeContextType = {
  preference: ThemePreference;
  resolvedTheme: ResolvedTheme;
  setPreference: (next: ThemePreference) => Promise<void>;
  accentColor: AccentColor;
  setAccentColor: (next: AccentColor) => Promise<void>;
  isSaving: boolean;
  isSavingAccent: boolean;
};

export const ThemeContext =
  createContext<ThemeContextType | null>(null);
