export interface Movement {
  name: string;
  signal: string;
}

export interface UserMovements {
  display_name: string;
  avatar: string;
  adds: Movement[];
  drops: Movement[];
}

export interface Transaction {
  transaction_id: string;
  league_name: string;
  time_ms: number;
  users: UserMovements[];
}

export interface Roster {
  league_name: string;
  players: string[];
}

export interface Orphan {
  league_name: string;
  roster_name: string;
  players: string[];
}

export interface Login {
  email: string;
  password: string;
}

export interface TradeRequest {
  league_id: string;
  k_adds: string[];
  v_adds: number[];
  k_drops: string[];
  v_drops: number[];
  draft_picks: string[];
  waiver_budget?: number[];
  expires_at?: number;
}

export interface WaiverRequest {
  league_id: string;
  k_adds: string[];
  v_adds: number[];
  k_drops: string[];
  v_drops: number[];
  draft_picks: string[];
  k_settings?: number[];
  v_settings?: number[];
}

export interface SendCodeRequest {
  username: string;
  captcha?: string;
}

export interface VerifyCodeRequest {
  username: string;
  code: string;
  captcha?: string;
}