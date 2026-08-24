import type { ValueBasis } from '@/types';

export const VALUE_BASIS_OPTIONS: Array<{
  value: ValueBasis;
  label: string;
}> = [
  { value: 'ktc', label: 'KTC Value' },
  { value: 'fantasycalc', label: 'FantasyCalc Value' },
  { value: 'adp', label: 'ADP Value' },
  { value: 'sleeper_projection', label: 'Sleeper projected points' },
  { value: 'dynasty_roster_war', label: 'Sleeper Projection Roster WAR' },
  { value: 'dynasty_starter_war', label: 'Sleeper Projection Starter WAR' },
  { value: 'my_roster_war', label: 'My Roster WAR' },
  { value: 'my_starter_war', label: 'My Starter WAR' },
];

export const LEGACY_WAR_BASIS_OPTIONS: Array<{
  value: ValueBasis;
  label: string;
}> = [
  {
    value: 'dynasty_roster_war',
    label: 'Dynasty Roster WAR',
  },
  {
    value: 'dynasty_starter_war',
    label: 'Dynasty Starter WAR',
  },
  {
    value: 'redraft_roster_war',
    label: 'Redraft Roster WAR',
  },
  {
    value: 'redraft_starter_war',
    label: 'Redraft Starter WAR',
  },
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


