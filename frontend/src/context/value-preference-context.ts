import { createContext } from 'react';

import type { ValueBasis } from '@/types';

export type ValuePreferenceContextType = {
  preference: ValueBasis;
  setPreference: (next: ValueBasis) => Promise<void>;
  isSaving: boolean;
};

export const ValuePreferenceContext =
  createContext<ValuePreferenceContextType | null>(null);
