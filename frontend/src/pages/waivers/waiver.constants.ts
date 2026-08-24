import type { ValueBasis } from '@/types';

export const VALUE_BASIS_OPTIONS: Array<{
  value: ValueBasis;
  label: string;
}> = [
  { value: 'ktc', label: 'KTC Value' },
  { value: 'fantasycalc', label: 'FantasyCalc Value' },
  { value: 'adp', label: 'ADP Value' },
  { value: 'sleeper_projection', label: 'Sleeper projected points' },
  { value: 'dynasty_roster_war', label: 'Dynasty Roster WAR' },
  { value: 'dynasty_starter_war', label: 'Dynasty Starter WAR' },
  { value: 'my_roster_war', label: 'My Roster WAR' },
  { value: 'my_starter_war', label: 'My Starter WAR' },
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
// redraft-meaningful projection/WAR sources.
const REDRAFT_VALUE_BASIS_OPTIONS: Array<{
  value: ValueBasis;
  label: string;
}> = [
  { value: 'sleeper_projection', label: 'Sleeper projected points' },
  { value: 'redraft_roster_war', label: 'Redraft Roster WAR' },
  { value: 'redraft_starter_war', label: 'Redraft Starter WAR' },
];

export function getRedraftValueBasisOptions(): Array<{
  value: ValueBasis;
  label: string;
}> {
  return REDRAFT_VALUE_BASIS_OPTIONS;
}
