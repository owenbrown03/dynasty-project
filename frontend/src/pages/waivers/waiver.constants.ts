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