import { useContext } from 'react';

import { ValuePreferenceContext } from '@/context/value-preference-context';

export function useValuePreference() {
  const context = useContext(
    ValuePreferenceContext,
  );

  if (!context) {
    throw new Error(
      'useValuePreference must be used within ValuePreferenceProvider',
    );
  }

  return context;
}
