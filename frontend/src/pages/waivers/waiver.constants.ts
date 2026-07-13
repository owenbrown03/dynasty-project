import type { ValueBasis } from '@/types';

export const VALUE_BASIS_OPTIONS: Array<{
  value: ValueBasis;
  label: string;
}> = [
  {
    value: 'ktc',
    label: 'KTC Value',
  },
  {
    value: 'fantasycalc',
    label: 'FantasyCalc Value',
  },
  {
    value: 'sleeper_war',
    label: 'Sleeper Projection WAR',
  },
  {
    value: 'my_war',
    label: 'My WAR',
  },
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
