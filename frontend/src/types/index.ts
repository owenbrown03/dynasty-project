export type Movement = {
  name: string;
  signal: string;
};

export type UserMovements = {
  display_name: string;
  avatar: string;
  adds: Movement[];
  drops: Movement[];
};

export type Transaction = {
  transaction_id: string;
  league_name: string;
  time_ms: number;
  users: UserMovements[];
};

export type Roster = {
  league_name: string;
  players: string[];
};

export type Orphan = {
  league_name: string;
  roster_name: string;
  players: string[];
};

export type Login = {
  email: string;
  password: string;
};

export type TradeRequest = {
  league_id: string;
  k_adds: string[];
  v_adds: number[];
  k_drops: string[];
  v_drops: number[];
  draft_picks: string[];
  waiver_budget?: number[];
  expires_at?: number;
};

export type WaiverRequest = {
  league_id: string;
  k_adds: string[];
  v_adds: number[];
  k_drops: string[];
  v_drops: number[];
  draft_picks: string[];
  k_settings?: number[];
  v_settings?: number[];
};

export type SendCodeRequest = {
  username: string;
  captcha: string;
};

export type SendCodeResponse = {
  connect_id: string;
};

export type VerifyCodeRequest = {
  connect_id: string;
  code: string;
  captcha?: string;
};

export type VerifyCodeResponse = {
  sleeper_token: string;
};

export type BootstrapUser = {
  id: string;
  email: string;
};

export type BootstrapSleeper = {
  linked: boolean;
  sleeper_username: string | null;
  sleeper_user_id: string | null;
  can_read: boolean;
  can_write: boolean;
};

export type Bootstrap = {
  authenticated: boolean;
  site_user: BootstrapUser | null;
  sleeper: BootstrapSleeper;
};

export type LeagueOverview = {
  league_id: string;
  league_name: string;
  season: string | null;
  total_rosters: number | null;
};

export type LeagueOwner = {
  user_id: string;
  display_name: string;
  avatar: string | null;
};

export type LeaguePlayer = {
  player_id: string;

  name: string;
  position: string;
  team: string | null;

  age: number | null;

  ktc_value: number | null;
  fc_value: number | null;

  starter_war: number | null;
  roster_war: number | null;
};

export type LeagueRoster = {
  roster_id: number;

  owner: LeagueOwner;

  total_starter_war: number;
  total_roster_war: number;

  rank: number;

  players: LeaguePlayer[];
};

export type LeagueDetails = {
  league_id: string;
  league_name: string;
  rosters: LeagueRoster[];
};

export type DashboardSummary = {
  league_count: number;
  player_count: number;
  total_ktc_value: number;
  total_fc_value: number;
  total_starter_war: number;
  total_roster_war: number;
  average_age: number;
};

export type DashboardLeague = {
  league_id: string;
  league_name: string;
  league_size: number;

  ktc_value: number;
  ktc_rank: number;

  fc_value: number;
  fc_rank: number;

  starter_war: number;
  starter_war_rank: number;

  roster_war: number;
  roster_war_rank: number;

  average_age: number | null;
  age_rank: number;
};

export type DashboardAsset = {
  player_id: string;
  name: string;
  position: string;
  team: string | null;

  ktc_value: number | null;
  fc_value: number | null;

  starter_war: number;
  roster_war: number;
};

export type Dashboard = {
  summary: DashboardSummary;
  leagues: DashboardLeague[];
  top_assets: DashboardAsset[];
};