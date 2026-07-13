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
    (option) => ![
      'sleeper_war',
      'my_war',
    ].includes(option.value),
  ),
  {
    value: 'league_war',
    label: 'League WAR',
  },
];


export const WAR_ONLY_OPTIONS = VALUE_BASIS_OPTIONS.filter(
  (option) => [
    'sleeper_war',
    'my_war',
  ].includes(
    option.value,
  ),
) as Array<{
  value: ValueBasis;
  label: string;
}>;
