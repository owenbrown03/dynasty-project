import type {
  DashboardLeague,
  LeaguePick,
  LeaguePlayer,
  LeagueRoster,
  ValueBasis,
  WarValueSettings,
} from '@/types';


function getSleeperProjectionMetricName(
  settings: WarValueSettings['sleeper_projection'],
): keyof LeaguePlayer {
  if (settings.timeframe === 'redraft') {
    return settings.scope === 'starter'
      ? 'redraft_starter_war'
      : 'redraft_roster_war';
  }

  return settings.scope === 'starter'
    ? 'dynasty_starter_war'
    : 'dynasty_roster_war';
}

function getMyProjectionMetricName(
  settings: WarValueSettings['my'],
): keyof LeaguePlayer {
  if (settings.timeframe === 'redraft') {
    return settings.scope === 'starter'
      ? 'my_redraft_starter_war'
      : 'my_redraft_roster_war';
  }

  return settings.scope === 'starter'
    ? 'my_dynasty_starter_war'
    : 'my_dynasty_roster_war';
}

function sumPlayerMetric(
  players: LeaguePlayer[],
  metricName: keyof LeaguePlayer,
): number {
  return players.reduce(
    (total, player) => total + Number(player[metricName] ?? 0),
    0,
  );
}

function getNumericPlayerMetric(
  player: LeaguePlayer,
  metricName: keyof LeaguePlayer,
): number | null {
  const value = player[metricName];

  return typeof value === 'number'
    ? value
    : null;
}

export function getValueBasisLabel(
  valueBasis: ValueBasis,
): string {
  switch (valueBasis) {
    case 'fantasycalc':
      return 'FantasyCalc';
    case 'adp':
      return 'ADP';
    case 'sleeper_war':
      return 'Sleeper WAR';
    case 'sleeper_projection':
      return 'Sleeper projected points';
    case 'my_war':
      return 'My WAR';
    case 'my_roster_war':
      return 'Dynasty Roster WAR';
    case 'my_starter_war':
      return 'Dynasty Starter WAR';
    case 'redraft_starter_war':
      return 'Redraft Starter WAR';
    case 'redraft_roster_war':
      return 'Redraft Roster WAR';
    case 'dynasty_starter_war':
      return 'Dynasty Starter WAR';
    case 'dynasty_roster_war':
      return 'Dynasty Roster WAR';
    case 'ktc_redraft':
      return 'KTC (redraft)';
    case 'fantasycalc_redraft':
      return 'FantasyCalc (redraft)';
    case 'ktc':
    default:
      return 'KTC';
  }
}

export function getLeaguePlayerSelectedValue(
  player: LeaguePlayer,
  valueBasis: ValueBasis,
  warValueSettings: WarValueSettings,
): number | null {
  switch (valueBasis) {
    case 'ktc':
      return player.ktc_value ?? null;
    case 'fantasycalc':
      return player.fc_value ?? null;
    case 'adp':
      return player.adp_value ?? null;
    case 'sleeper_projection':
      return player.projected_points ?? null;
    case 'redraft_starter_war':
      return player.redraft_starter_war ?? null;
    case 'redraft_roster_war':
      return player.redraft_roster_war ?? null;
    case 'dynasty_starter_war':
      return player.dynasty_starter_war ?? null;
    case 'dynasty_roster_war':
      return player.dynasty_roster_war ?? null;
    case 'ktc_redraft':
      return player.ktc_redraft_value ?? null;
    case 'fantasycalc_redraft':
      return player.fc_redraft_value ?? null;
    case 'sleeper_war':
      return getNumericPlayerMetric(
        player,
        getSleeperProjectionMetricName(
          warValueSettings.sleeper_projection,
        ),
      );
    case 'my_roster_war':
      return player.my_dynasty_roster_war ?? null;
    case 'my_starter_war':
      return player.my_dynasty_starter_war ?? null;
    case 'my_war':
      return getNumericPlayerMetric(
        player,
        getMyProjectionMetricName(
          warValueSettings.my,
        ),
      );
    default:
      return null;
  }
}

export function getRosterSelectedAssetValue(
  roster: LeagueRoster,
  valueBasis: ValueBasis,
  warValueSettings: WarValueSettings,
): number | null {
  switch (valueBasis) {
    case 'ktc':
      return roster.total_asset_ktc_value;
    case 'fantasycalc':
      return roster.total_asset_fc_value;
    case 'adp':
      return sumPlayerMetric(roster.players, 'adp_value');
    case 'redraft_starter_war':
      return roster.total_redraft_starter_war;
    case 'redraft_roster_war':
      return roster.total_redraft_roster_war;
    case 'dynasty_starter_war':
      return roster.total_dynasty_starter_war;
    case 'dynasty_roster_war':
      return roster.total_dynasty_roster_war;
    case 'ktc_redraft':
      return sumPlayerMetric(roster.players, 'ktc_redraft_value');
    case 'fantasycalc_redraft':
      return sumPlayerMetric(roster.players, 'fc_redraft_value');
    case 'sleeper_war':
      return sumPlayerMetric(
        roster.players,
        getSleeperProjectionMetricName(
          warValueSettings.sleeper_projection,
        ),
      );
    case 'sleeper_projection':
      return sumPlayerMetric(
        roster.players,
        'projected_points',
      );
    case 'my_roster_war':
      return sumPlayerMetric(
        roster.players,
        'my_dynasty_roster_war',
      );
    case 'my_starter_war':
      return sumPlayerMetric(
        roster.players,
        'my_dynasty_starter_war',
      );
    case 'my_war':
      return sumPlayerMetric(
        roster.players,
        getMyProjectionMetricName(
          warValueSettings.my,
        ),
      );
    default:
      return null;
  }
}

export function getRosterSelectedPlayerValue(
  roster: LeagueRoster,
  valueBasis: ValueBasis,
  warValueSettings: WarValueSettings,
): number | null {
  switch (valueBasis) {
    case 'ktc':
      return roster.total_ktc_value;
    case 'fantasycalc':
      return roster.total_fc_value;
    case 'adp':
      return sumPlayerMetric(roster.players, 'adp_value');
    case 'redraft_starter_war':
      return roster.total_redraft_starter_war;
    case 'redraft_roster_war':
      return roster.total_redraft_roster_war;
    case 'dynasty_starter_war':
      return roster.total_dynasty_starter_war;
    case 'dynasty_roster_war':
      return roster.total_dynasty_roster_war;
    case 'ktc_redraft':
      return sumPlayerMetric(roster.players, 'ktc_redraft_value');
    case 'fantasycalc_redraft':
      return sumPlayerMetric(roster.players, 'fc_redraft_value');
    case 'sleeper_war':
      return sumPlayerMetric(
        roster.players,
        getSleeperProjectionMetricName(
          warValueSettings.sleeper_projection,
        ),
      );
    case 'sleeper_projection':
      return sumPlayerMetric(
        roster.players,
        'projected_points',
      );
    case 'my_roster_war':
      return sumPlayerMetric(
        roster.players,
        'my_dynasty_roster_war',
      );
    case 'my_starter_war':
      return sumPlayerMetric(
        roster.players,
        'my_dynasty_starter_war',
      );
    case 'my_war':
      return sumPlayerMetric(
        roster.players,
        getMyProjectionMetricName(
          warValueSettings.my,
        ),
      );
    default:
      return null;
  }
}

export function getRosterSelectedPickValue(
  roster: LeagueRoster,
  valueBasis: ValueBasis,
): number | null {
  switch (valueBasis) {
    case 'ktc':
      return roster.total_pick_ktc_value;
    case 'fantasycalc':
      return roster.total_pick_fc_value;
    case 'redraft_starter_war':
    case 'redraft_roster_war':
    case 'dynasty_starter_war':
    case 'dynasty_roster_war':
    case 'sleeper_war':
    case 'my_war':
    case 'my_roster_war':
    case 'my_starter_war':
    case 'sleeper_projection':
    case 'ktc_redraft':
    case 'fantasycalc_redraft':
      return roster.total_pick_rookie_war_value;
    default:
      return null;
  }
}

export function getRosterSelectedAssetRank(
  roster: LeagueRoster,
  valueBasis: ValueBasis,
  warValueSettings: WarValueSettings,
): number | undefined {
  const settings = warValueSettings.sleeper_projection;
  const mySettings = warValueSettings.my;

  switch (valueBasis) {
    case 'ktc':
      return roster.stat_ranks.total_asset_ktc_value;
    case 'fantasycalc':
      return roster.stat_ranks.total_asset_fc_value;
    case 'redraft_starter_war':
      return roster.stat_ranks.total_redraft_starter_war;
    case 'redraft_roster_war':
      return roster.stat_ranks.total_redraft_roster_war;
    case 'dynasty_starter_war':
      return roster.stat_ranks.total_dynasty_starter_war;
    case 'dynasty_roster_war':
      return roster.stat_ranks.total_dynasty_roster_war;
    case 'sleeper_war':
      if (settings.timeframe === 'redraft') {
        return settings.scope === 'starter'
          ? roster.stat_ranks.total_redraft_starter_war
          : roster.stat_ranks.total_redraft_roster_war;
      }

      return settings.scope === 'starter'
        ? roster.stat_ranks.total_dynasty_starter_war
        : roster.stat_ranks.total_dynasty_roster_war;
    case 'my_war':
      if (mySettings.timeframe === 'redraft') {
        return mySettings.scope === 'starter'
          ? roster.stat_ranks.total_redraft_starter_war
          : roster.stat_ranks.total_redraft_roster_war;
      }

      return mySettings.scope === 'starter'
        ? roster.stat_ranks.total_dynasty_starter_war
        : roster.stat_ranks.total_dynasty_roster_war;
    case 'my_roster_war':
      return roster.stat_ranks.total_dynasty_roster_war;
    case 'my_starter_war':
      return roster.stat_ranks.total_dynasty_starter_war;
    case 'sleeper_projection':
      return roster.stat_ranks.projected_points;
    default:
      return undefined;
  }
}

export function getRosterSelectedPlayerRank(
  roster: LeagueRoster,
  valueBasis: ValueBasis,
  warValueSettings: WarValueSettings,
): number | undefined {
  return getRosterSelectedAssetRank(
    roster,
    valueBasis,
    warValueSettings,
  );
}

export function getRosterSelectedPickRank(
  roster: LeagueRoster,
  valueBasis: ValueBasis,
): number | undefined {
  switch (valueBasis) {
    case 'ktc':
      return roster.stat_ranks.total_pick_ktc_value;
    case 'fantasycalc':
      return roster.stat_ranks.total_pick_fc_value;
    case 'redraft_starter_war':
    case 'redraft_roster_war':
    case 'dynasty_starter_war':
    case 'dynasty_roster_war':
    case 'sleeper_war':
    case 'my_war':
    case 'my_roster_war':
    case 'my_starter_war':
    case 'sleeper_projection':
    case 'ktc_redraft':
    case 'fantasycalc_redraft':
      return roster.stat_ranks.total_pick_rookie_war_value;
    default:
      return undefined;
  }
}

export function getPickSelectedValue(
  pick: LeaguePick,
  valueBasis: ValueBasis,
): number | null {
  switch (valueBasis) {
    case 'ktc':
      return pick.ktc_value;
    case 'fantasycalc':
      return pick.fc_value;
    case 'redraft_starter_war':
    case 'redraft_roster_war':
    case 'dynasty_starter_war':
    case 'dynasty_roster_war':
    case 'sleeper_war':
    case 'my_war':
    case 'my_roster_war':
    case 'my_starter_war':
    case 'sleeper_projection':
    case 'ktc_redraft':
    case 'fantasycalc_redraft':
      return pick.rookie_war_value;
    default:
      return null;
  }
}

export function getPickValueLabel(
  valueBasis: ValueBasis,
): string {
  switch (valueBasis) {
    case 'ktc':
      return 'KTC Pick Value';
    case 'fantasycalc':
      return 'FantasyCalc Pick Value';
    default:
      return 'WAR';
  }
}

export function getDashboardLeagueSelectedValue(
  league: DashboardLeague,
  valueBasis: ValueBasis,
  warValueSettings?: WarValueSettings,
): number | null {
  const mySettings = warValueSettings?.my;

  switch (valueBasis) {
    case 'ktc':
      return league.ktc_value;
    case 'fantasycalc':
      return league.fc_value;
    case 'redraft_starter_war':
      return league.redraft_starter_war;
    case 'redraft_roster_war':
      return league.redraft_roster_war;
    case 'dynasty_starter_war':
      return league.dynasty_starter_war;
    case 'dynasty_roster_war':
    case 'sleeper_war':
      return league.dynasty_roster_war;
    case 'sleeper_projection':
      return league.redraft_roster_war ?? null;
    case 'my_roster_war':
      return league.my_dynasty_roster_war ?? null;
    case 'my_starter_war':
      return league.my_dynasty_starter_war ?? null;
    case 'my_war':
      if (mySettings?.timeframe === 'redraft') {
        return mySettings.scope === 'starter'
          ? league.my_redraft_starter_war ?? null
          : league.my_redraft_roster_war ?? null;
      }

      return mySettings?.scope === 'starter'
        ? league.my_dynasty_starter_war ?? null
        : league.my_dynasty_roster_war ?? null;
    default:
      return league.ktc_value;
  }
}

export function getDashboardLeagueSelectedRank(
  league: DashboardLeague,
  valueBasis: ValueBasis,
  warValueSettings?: WarValueSettings,
): number | null {
  const mySettings = warValueSettings?.my;

  switch (valueBasis) {
    case 'ktc':
      return league.ktc_rank;
    case 'fantasycalc':
      return league.fc_rank;
    case 'redraft_starter_war':
      return league.redraft_starter_war_rank;
    case 'redraft_roster_war':
      return league.redraft_roster_war_rank;
    case 'dynasty_starter_war':
      return league.dynasty_starter_war_rank;
    case 'dynasty_roster_war':
    case 'sleeper_war':
      return league.dynasty_roster_war_rank;
    case 'my_war':
      if (mySettings?.timeframe === 'redraft') {
        return mySettings.scope === 'starter'
          ? league.my_redraft_starter_war_rank ?? null
          : league.my_redraft_roster_war_rank ?? null;
      }

      return mySettings?.scope === 'starter'
        ? league.my_dynasty_starter_war_rank ?? null
        : league.my_dynasty_roster_war_rank ?? null;
    default:
      return league.ktc_rank;
  }
}

const DYNASTY_WAR_SCOPE_BASES: ValueBasis[] = [
  'dynasty_roster_war',
  'dynasty_starter_war',
  'my_roster_war',
  'my_starter_war',
];

const REDRAFT_WAR_SCOPE_BASES: ValueBasis[] = [
  'redraft_roster_war',
  'redraft_starter_war',
];

// Roster-summary WAR stats. These always resolve to a dynasty/redraft
// WAR number (never points or market prices) so the labels stay
// truthful. When the user's system is itself a WAR basis the value
// follows its scope (starter vs roster, personal vs market);
// otherwise it falls back to the full-roster market WAR leg.
export function getRosterDynastyWAR(
  roster: LeagueRoster,
  valueBasis: ValueBasis,
  warValueSettings: WarValueSettings,
): number | null {
  if (DYNASTY_WAR_SCOPE_BASES.includes(valueBasis)) {
    return getRosterSelectedPlayerValue(
      roster,
      valueBasis,
      warValueSettings,
    );
  }

  return roster.total_dynasty_roster_war;
}

export function getRosterDynastyWARRank(
  roster: LeagueRoster,
  valueBasis: ValueBasis,
  warValueSettings: WarValueSettings,
): number | undefined {
  if (DYNASTY_WAR_SCOPE_BASES.includes(valueBasis)) {
    return getRosterSelectedPlayerRank(
      roster,
      valueBasis,
      warValueSettings,
    );
  }

  return roster.stat_ranks.total_dynasty_roster_war;
}

export function getRosterRedraftWAR(
  roster: LeagueRoster,
  redraftValueBasis: ValueBasis | undefined,
  warValueSettings: WarValueSettings,
): number | null {
  if (
    redraftValueBasis
    && REDRAFT_WAR_SCOPE_BASES.includes(redraftValueBasis)
  ) {
    return getRosterSelectedPlayerValue(
      roster,
      redraftValueBasis,
      warValueSettings,
    );
  }

  return roster.total_redraft_roster_war;
}

export function getRosterRedraftWARRank(
  roster: LeagueRoster,
  redraftValueBasis: ValueBasis | undefined,
  warValueSettings: WarValueSettings,
): number | undefined {
  if (
    redraftValueBasis
    && REDRAFT_WAR_SCOPE_BASES.includes(redraftValueBasis)
  ) {
    return getRosterSelectedPlayerRank(
      roster,
      redraftValueBasis,
      warValueSettings,
    );
  }

  return roster.stat_ranks.total_redraft_roster_war;
}
