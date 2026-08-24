import type { ValueBasis } from '@/types';

export const VALUE_PREFERENCE_STORAGE_KEY =
  'dynasty-value-preference';

export function isValuePreference(
  value: string | null,
): value is ValueBasis {
  return value === 'ktc'
    || value === 'fantasycalc'
    || value === 'adp'
    || value === 'sleeper_war'
    || value === 'my_war'
    || value === 'dynasty_starter_war'
    || value === 'dynasty_roster_war'
    || value === 'redraft_starter_war'
    || value === 'redraft_roster_war';
}

export function getStoredValuePreference(): ValueBasis {
  if (typeof window === 'undefined') {
    return 'ktc';
  }

  const stored = window.localStorage.getItem(
    VALUE_PREFERENCE_STORAGE_KEY,
  );

  if (isValuePreference(stored)) {
    return stored;
  }

  return 'ktc';
}


export const REDRAFT_VALUE_PREFERENCE_STORAGE_KEY =
  'dynasty-redraft-value-preference';

const REDRAFT_VALUE_PREFERENCES: ValueBasis[] = [
  'ktc',
  'fantasycalc',
  'adp',
];

export function getStoredRedraftValuePreference(): ValueBasis {
  if (typeof window === 'undefined') {
    return 'ktc';
  }

  const stored = window.localStorage.getItem(
    REDRAFT_VALUE_PREFERENCE_STORAGE_KEY,
  );

  if (
    stored
    && REDRAFT_VALUE_PREFERENCES.includes(
      stored as ValueBasis,
    )
  ) {
    return stored as ValueBasis;
  }

  return 'ktc';
}
