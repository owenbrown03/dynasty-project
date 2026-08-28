import type { ValueBasis } from '@/types';

export const VALUE_BASIS_OPTIONS: Array<{
  value: ValueBasis;
  label: string;
}> = [
  { value: 'ktc', label: 'KTC Value' },
  { value: 'fantasycalc', label: 'FantasyCalc Value' },
  { value: 'adp', label: 'ADP Value' },
  { value: 'my_roster_war', label: 'Dynasty Roster WAR' },
  { value: 'my_starter_war', label: 'Dynasty Starter WAR' },
];

export function getValueBasisOptions(
  includePersonal: boolean,
) {
  return VALUE_BASIS_OPTIONS.filter(
    (option) => (
      includePersonal
      || option.value !== 'my_war'
    ),
  );
}


// Redraft Value assigns per-player redraft valuations (#165): the
// redraft-meaningful projection/WAR/market sources. Sleeper projected
// points is redraft-only (no dynasty multi-year projection), and the
// KTC/FantasyCalc entries use their redraft market rows.
const REDRAFT_VALUE_BASIS_OPTIONS: Array<{
  value: ValueBasis;
  label: string;
}> = [
  { value: 'sleeper_projection', label: 'Sleeper projected points' },
  { value: 'ktc_redraft', label: 'KTC (redraft)' },
  { value: 'fantasycalc_redraft', label: 'FantasyCalc (redraft)' },
  { value: 'redraft_roster_war', label: 'Redraft Roster WAR' },
  { value: 'redraft_starter_war', label: 'Redraft Starter WAR' },
];

export function getRedraftValueBasisOptions(): Array<{
  value: ValueBasis;
  label: string;
}> {
  return REDRAFT_VALUE_BASIS_OPTIONS;
}
