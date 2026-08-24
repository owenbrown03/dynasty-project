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
  'redraft_roster_war',
  'redraft_starter_war',
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

// Selector surfaces offer the same pool as the settings picker
// (#165 principle). League-context bases simply require a league.
export const TIER_SOURCE_OPTIONS: Array<{
  value: TierBoardSource;
  label: string;
}> = [
  ...VALUE_BASIS_OPTIONS,
  { value: 'redraft_roster_war', label: 'Redraft Roster WAR' },
  { value: 'redraft_starter_war', label: 'Redraft Starter WAR' },
];

