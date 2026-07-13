import type {
  TierBoardSource,
  ValueBasis,
} from '@/types';
import { VALUE_BASIS_OPTIONS } from '@/pages/waivers/waiver.constants';


export const TIER_SOURCE_OPTIONS: Array<{
  value: TierBoardSource;
  label: string;
}> = [
  ...VALUE_BASIS_OPTIONS.filter(
    (option) => option.value !== 'my_war',
  ),
  {
    value: 'league_war',
    label: 'League WAR',
  },
];


export const WAR_ONLY_OPTIONS = VALUE_BASIS_OPTIONS.filter(
  (option) => [
    'dynasty_roster_war',
    'dynasty_starter_war',
    'redraft_roster_war',
    'redraft_starter_war',
    'my_war',
  ].includes(
    option.value,
  ),
) as Array<{
  value: ValueBasis;
  label: string;
}>;
