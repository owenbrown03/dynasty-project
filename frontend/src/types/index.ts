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

export type SleeperConnection = {
  sleeper_user_id: string | null;
  username: string | null;
  can_read: boolean;
  can_write: boolean;
};

export type MeRequest = {
  authenticated: boolean;
  user: string | null;
};