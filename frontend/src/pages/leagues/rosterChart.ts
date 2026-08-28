import type { LeagueDetails, LeagueRoster } from "@/types";

export type RosterStatKey =
  | "dynasty_roster_war"
  | "dynasty_starter_war"
  | "redraft_roster_war"
  | "redraft_starter_war"
  | "pick_rookie_war"
  | "total_asset_ktc_value"
  | "total_ktc_value"
  | "total_pick_ktc_value"
  | "total_asset_fc_value"
  | "total_fc_value"
  | "total_pick_fc_value"
  | "projected_points"
  | "actual_points_for"
  | "wins"
  | "average_age"
  | "open_roster_spots"
  | "faab_remaining"
  | "total_moves"
  | "total_trades";

export interface RosterStatOption {
  key: RosterStatKey;
  label: string;
  group: "WAR" | "Market Values" | "Scoring & Record" | "Roster Construction";
  shortLabel: string;
}

export const ROSTER_STAT_OPTIONS: RosterStatOption[] = [
  // WAR
  { key: "dynasty_roster_war", label: "Dynasty WAR (Roster)", group: "WAR", shortLabel: "Dynasty Roster WAR" },
  { key: "dynasty_starter_war", label: "Dynasty WAR (Starters)", group: "WAR", shortLabel: "Dynasty Starter WAR" },
  { key: "redraft_roster_war", label: "Redraft WAR (Roster)", group: "WAR", shortLabel: "Redraft Roster WAR" },
  { key: "redraft_starter_war", label: "Redraft WAR (Starters)", group: "WAR", shortLabel: "Redraft Starter WAR" },
  { key: "pick_rookie_war", label: "Pick WAR (Rookies)", group: "WAR", shortLabel: "Pick WAR" },

  // Market Values
  { key: "total_asset_ktc_value", label: "KTC Value (Total Assets)", group: "Market Values", shortLabel: "KTC Asset Value" },
  { key: "total_ktc_value", label: "KTC Value (Players Only)", group: "Market Values", shortLabel: "KTC Player Value" },
  { key: "total_pick_ktc_value", label: "KTC Value (Picks Only)", group: "Market Values", shortLabel: "KTC Pick Value" },
  { key: "total_asset_fc_value", label: "FantasyCalc Value (Total Assets)", group: "Market Values", shortLabel: "FC Asset Value" },
  { key: "total_fc_value", label: "FantasyCalc Value (Players Only)", group: "Market Values", shortLabel: "FC Player Value" },
  { key: "total_pick_fc_value", label: "FantasyCalc Value (Picks Only)", group: "Market Values", shortLabel: "FC Pick Value" },

  // Scoring & Record
  { key: "projected_points", label: "Projected Points", group: "Scoring & Record", shortLabel: "Projected Points" },
  { key: "actual_points_for", label: "Points For (Actual)", group: "Scoring & Record", shortLabel: "Points For" },
  { key: "wins", label: "Wins", group: "Scoring & Record", shortLabel: "Wins" },

  // Roster Construction
  { key: "average_age", label: "Average Age", group: "Roster Construction", shortLabel: "Average Age" },
  { key: "open_roster_spots", label: "Open Roster Spots", group: "Roster Construction", shortLabel: "Open Spots" },
  { key: "faab_remaining", label: "FAAB Remaining", group: "Roster Construction", shortLabel: "FAAB Remaining" },
  { key: "total_moves", label: "Total Moves (Waivers + Free Agents)", group: "Roster Construction", shortLabel: "Total Moves" },
  { key: "total_trades", label: "Total Trades", group: "Roster Construction", shortLabel: "Total Trades" },
];

export function getRosterStatValue(
  roster: LeagueRoster,
  statKey: RosterStatKey,
): number | null {
  switch (statKey) {
    case "dynasty_roster_war":
      return roster.total_dynasty_roster_war ?? 0;
    case "dynasty_starter_war":
      return roster.total_dynasty_starter_war ?? 0;
    case "redraft_roster_war":
      return roster.total_redraft_roster_war ?? 0;
    case "redraft_starter_war":
      return roster.total_redraft_starter_war ?? 0;
    case "pick_rookie_war":
      return roster.total_pick_rookie_war_value ?? 0;
    case "total_asset_ktc_value":
      return roster.total_asset_ktc_value ?? 0;
    case "total_ktc_value":
      return roster.total_ktc_value ?? 0;
    case "total_pick_ktc_value":
      return roster.total_pick_ktc_value ?? 0;
    case "total_asset_fc_value":
      return roster.total_asset_fc_value ?? 0;
    case "total_fc_value":
      return roster.total_fc_value ?? 0;
    case "total_pick_fc_value":
      return roster.total_pick_fc_value ?? 0;
    case "projected_points":
      return roster.projected_points ?? 0;
    case "actual_points_for":
      return roster.actual_points_for ?? 0;
    case "wins":
      return roster.wins ?? 0;
    case "average_age":
      return roster.average_age;
    case "open_roster_spots":
      return roster.open_roster_spots ?? 0;
    case "faab_remaining":
      return roster.faab_remaining ?? 0;
    case "total_moves":
      return roster.total_moves ?? 0;
    case "total_trades":
      return roster.total_trades ?? 0;
    default:
      return null;
  }
}

export function formatRosterStatValue(
  val: number | null,
  statKey: RosterStatKey,
): string {
  if (val === null || val === undefined) {
    return "—";
  }

  switch (statKey) {
    case "dynasty_roster_war":
    case "dynasty_starter_war":
    case "redraft_roster_war":
    case "redraft_starter_war":
    case "pick_rookie_war":
      return `${val.toFixed(2)} WAR`;
    case "total_asset_ktc_value":
    case "total_ktc_value":
    case "total_pick_ktc_value":
      return `${Math.round(val).toLocaleString("en-US")} KTC`;
    case "total_asset_fc_value":
    case "total_fc_value":
    case "total_pick_fc_value":
      return `${Math.round(val).toLocaleString("en-US")} FC`;
    case "projected_points":
    case "actual_points_for":
      return `${val.toLocaleString("en-US", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} pts`;
    case "wins":
      return `${val} win${val === 1 ? "" : "s"}`;
    case "average_age":
      return `${val.toFixed(1)} yrs`;
    case "open_roster_spots":
      return `${val} spot${val === 1 ? "" : "s"}`;
    case "faab_remaining":
      return `$${Math.round(val).toLocaleString("en-US")}`;
    case "total_moves":
      return `${val} move${val === 1 ? "" : "s"}`;
    case "total_trades":
      return `${val} trade${val === 1 ? "" : "s"}`;
    default:
      return String(val);
  }
}

export function sortRostersByStat(
  rosters: LeagueRoster[],
  statKey: RosterStatKey,
  direction: "desc" | "asc" = "desc",
): LeagueRoster[] {
  return [...rosters].sort((a, b) => {
    const valA = getRosterStatValue(a, statKey);
    const valB = getRosterStatValue(b, statKey);

    if (valA === null && valB === null) return 0;
    if (valA === null) return 1;
    if (valB === null) return -1;

    if (direction === "desc") {
      if (valB !== valA) return valB - valA;
    } else {
      if (valA !== valB) return valA - valB;
    }

    if (a.rank !== b.rank) return a.rank - b.rank;
    return a.roster_id - b.roster_id;
  });
}

export interface RosterStatSummary {
  max: number | null;
  min: number | null;
  avg: number | null;
  userRank: number | null;
  userValue: number | null;
}

export function computeRosterStatSummary(
  league: LeagueDetails,
  sortedRosters: LeagueRoster[],
  statKey: RosterStatKey,
  currentUserId?: string | null,
): RosterStatSummary {
  const numericValues = league.rosters
    .map((r) => getRosterStatValue(r, statKey))
    .filter((v): v is number => v !== null);

  if (!numericValues.length) {
    return {
      max: null,
      min: null,
      avg: null,
      userRank: null,
      userValue: null,
    };
  }

  const max = Math.max(...numericValues);
  const min = Math.min(...numericValues);
  const sum = numericValues.reduce((acc, v) => acc + v, 0);
  const avg = sum / numericValues.length;

  let userRank: number | null = null;
  let userValue: number | null = null;

  if (currentUserId) {
    const userRosterIndex = sortedRosters.findIndex(
      (r) => r.owner?.user_id === currentUserId,
    );
    if (userRosterIndex !== -1) {
      userRank = userRosterIndex + 1;
      userValue = getRosterStatValue(sortedRosters[userRosterIndex], statKey);
    }
  }

  return {
    max,
    min,
    avg,
    userRank,
    userValue,
  };
}
