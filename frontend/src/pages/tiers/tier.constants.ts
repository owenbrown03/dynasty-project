import type {
  TierBoardSource,
  ValueBasis,
} from '@/types';
import { VALUE_BASIS_OPTIONS } from '@/pages/waivers/waiver.constants';

/**
 * Value bases that are computed from a league's redraft context and
 * therefore cannot be used without selecting a league. Single source
 * of truth for both tier-board source lists - keep the backend's
 * load_player_values_for_basis in sync with this classification.
 */
export const LEAGUE_CONTEXT_VALUE_BASES: ValueBasis[] = [
  'sleeper_war',
  'my_roster_war',
  'my_starter_war',
  'dynasty_roster_war',
  'dynasty_starter_war',
  'sleeper_projection',
];

export function isLeagueContextValueBasis(
  value: ValueBasis,
): boolean {
  return LEAGUE_CONTEXT_VALUE_BASES.includes(value);
}

export const TIER_SOURCE_OPTIONS: Array<{
  value: TierBoardSource;
  label: string;
}> = [
  ...VALUE_BASIS_OPTIONS.filter(
    (option) => !isLeagueContextValueBasis(option.value),
  ),
  {
    value: 'league_war',
    label: 'League WAR',
  },
];

const LEAGUE_CONTEXT_LABELS: Partial<Record<ValueBasis, string>> = {
  sleeper_war: 'Sleeper WAR',
  my_roster_war: 'My Roster WAR',
  my_starter_war: 'My Starter WAR',
  dynasty_roster_war: 'Sleeper Projection Roster WAR',
  dynasty_starter_war: 'Sleeper Projection Starter WAR',
  sleeper_projection: 'Sleeper projected points',
};

// Built from the league-context set directly so the legacy
// sleeper_war basis remains selectable under League WAR even though
// it is no longer part of the main picker pool.
export const WAR_ONLY_OPTIONS = LEAGUE_CONTEXT_VALUE_BASES.map(
  (value) => ({
    value,
    label:
      VALUE_BASIS_OPTIONS.find(
        (option) => option.value === value,
      )?.label ?? LEAGUE_CONTEXT_LABELS[value] ?? value,
  }),
);

