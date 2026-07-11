import { createContext } from 'react';

import type { ThemePreference } from '@/types';

type ResolvedTheme = 'light' | 'dark';

export type ThemeContextType = {
  preference: ThemePreference;
  resolvedTheme: ResolvedTheme;
  setPreference: (next: ThemePreference) => Promise<void>;
  isSaving: boolean;
};

export const ThemeContext =
  createContext<ThemeContextType | null>(null);
