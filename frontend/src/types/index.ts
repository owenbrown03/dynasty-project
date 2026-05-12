export interface Movement {
  name: string;
  signal: string;
}

export interface User {
  display_name: string;
  avatar: string;
  adds: Movement[];
  drops: Movement[];
}

export interface Transaction {
  transaction_id: string;
  league_name: string;
  time_ms: number;
  users: User[];
}