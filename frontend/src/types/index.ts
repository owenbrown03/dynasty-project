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