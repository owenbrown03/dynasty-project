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
  players: OrphanPlayer[];
}

export interface OrphanPlayer {
  player_id: string | null;
  name: string;
  position: string | null;
  team: string | null;
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
  captcha: string;
}

export interface SendCodeResponse {
  connect_id: string;
}

export interface VerifyCodeRequest {
  connect_id: string;
  code: string;
  captcha?: string;
}

export interface VerifyCodeResponse {
  sleeper_token: string;
}

export interface BootstrapUser {
  id: string;
  email: string;
}

export interface BootstrapSleeper {
  linked: boolean;
  sleeper_username: string | null;
  sleeper_user_id: string | null;
  can_read: boolean;
  can_write: boolean;
}

export interface SleeperConnection {
  linked: boolean;
  sleeper_username: string | null;
  sleeper_user_id: string | null;
  can_read: boolean;
  can_write: boolean;
}

export interface Bootstrap {
  authenticated: boolean;
  site_user: BootstrapUser | null;
  sleeper: BootstrapSleeper;
  theme_preference: ThemePreference | null;
}

export type ThemePreference =
  | 'light'
  | 'dark'
  | 'system';

export interface LeagueOverview {
  league_id: string;
  league_name: string;
  season: string | null;
  total_rosters: number | null;
}

export interface LeagueOwner {
  user_id: string | null;
  display_name: string;
  avatar: string | null;
}

export interface LeagueSettingsDetail {
  label: string;
  value: string;
}

export interface LeaguePick {
  season: string;
  round: number;
  og_roster_id: number;
  current_owner_roster_id: number;
  label: string;
  slot: number | null;
  fc_value: number | null;
  ktc_value: number | null;
}

export interface LeaguePlayer {
  player_id: string;

  name: string;
  position: string | null;
  team: string | null;

  age: number | null;
  underdog_position_rank: string | null;
  projected_points: number | null;

  ktc_value: number | null;
  fc_value: number | null;
  fc_trend_30_day: number | null;

  redraft_starter_war: number | null;
  redraft_roster_war: number | null;
  dynasty_starter_war: number | null;
  dynasty_roster_war: number | null;
  is_starter: boolean;
}

export interface LeagueRoster {
  roster_id: number;

  owner: LeagueOwner;
  record: string;
  wins: number;
  losses: number;
  ties: number;
  actual_points_for: number;
  projected_points: number;
  faab_remaining: number;
  waiver_position: number;
  total_moves: number;
  open_roster_spots: number;
  average_age: number | null;
  total_ktc_value: number;
  total_fc_value: number;
  total_redraft_starter_war: number;
  total_redraft_roster_war: number;
  total_dynasty_starter_war: number;
  total_dynasty_roster_war: number;
  total_pick_ktc_value: number;
  total_pick_fc_value: number;
  total_asset_ktc_value: number;
  total_asset_fc_value: number;

  rank: number;

  players: LeaguePlayer[];
  picks: LeaguePick[];
}

export interface LeagueDetails {
  league_id: string;
  league_name: string;
  season: string;
  total_rosters: number;
  settings_badges: string[];
  settings_details: LeagueSettingsDetail[];
  rosters: LeagueRoster[];
}

export interface DashboardSummary {
  league_count: number;
  player_count: number;
  total_ktc_value: number;
  total_fc_value: number;
  total_dynasty_starter_war: number;
  total_dynasty_roster_war: number;
  total_redraft_starter_war: number;
  total_redraft_roster_war: number;
  average_age: number;
}

export interface DashboardLeague {
  league_id: string;
  league_name: string;
  league_size: number;

  ktc_value: number;
  ktc_rank: number;

  fc_value: number;
  fc_rank: number;

  dynasty_starter_war: number;
  dynasty_starter_war_rank: number;

  dynasty_roster_war: number;
  dynasty_roster_war_rank: number;

  redraft_starter_war: number;
  redraft_starter_war_rank: number;

  redraft_roster_war: number;
  redraft_roster_war_rank: number;

  average_age: number | null;
  age_rank: number;
}

export interface DashboardAsset {
  player_id: string;
  name: string;
  position: string;
  team: string | null;

  ktc_value: number | null;
  fc_value: number | null;

  starter_war: number | null;
  roster_war: number | null;
}

export interface Dashboard {
  summary: DashboardSummary;
  leagues: DashboardLeague[];
  top_assets: DashboardAsset[];
}

export type ValueBasis =
  | 'ktc'
  | 'fantasycalc'
  | 'redraft_starter_war'
  | 'redraft_roster_war'
  | 'dynasty_starter_war'
  | 'dynasty_roster_war';

export type TierBoardSource =
  | ValueBasis
  | 'league_war';

export interface TierBoardPlayer {
  player_id: string;
  name: string;
  position: string | null;
  team: string | null;
  age: number | null;
  rank: number;
  tier: string;
  selected_value: number;
}

export interface TierBoardGroup {
  label: string;
  players: TierBoardPlayer[];
}

export interface TierBoard {
  value_basis: ValueBasis;
  value_label: string;
  season: number;
  war_context: string;
  war_league_id: string | null;
  war_league_name: string | null;
  tiers: TierBoardGroup[];
}

export interface CommissionerPlayerAsset {
  player_id: string;
  name: string;
  position: string | null;
  team: string | null;
  age: number | null;
  selected_value: number | null;
}

export interface CommissionerLineupSlot {
  slot: string;
  player: CommissionerPlayerAsset | null;
}

export interface CommissionerDraftPickAsset {
  season: string;
  round: number;
  og_roster_id: number;
  current_owner_roster_id: number;
  original_owner_name: string | null;
  current_owner_name: string | null;
  slot: number | null;
  label: string;
  selected_value: number | null;
  value_source_label: string | null;
}

export interface CommissionerOrphanRoster {
  league_id: string;
  league_name: string;
  league_season: string;
  roster_id: number;
  roster_name: string;
  settings_badges: string[];
  roster_value: number;
  league_average_value: number;
  average_age: number | null;
  lineup: CommissionerLineupSlot[];
  bench: CommissionerPlayerAsset[];
  picks: CommissionerDraftPickAsset[];
}

export interface CommissionerOrphansResponse {
  username: string;
  value_basis: ValueBasis;
  value_label: string;
  orphans: CommissionerOrphanRoster[];
}

export interface PlayerValue {
  player_id: string;

  name: string;
  position: string | null;
  team: string | null;
  age: number | null;

  ktc_value: number | null;
  fc_value: number | null;
  underdog_position_rank: string | null;

  redraft_starter_war: number | null;
  redraft_roster_war: number | null;

  dynasty_starter_war: number | null;
  dynasty_roster_war: number | null;

  dynasty_expected_games_remaining: number | null;
  dynasty_seasons_remaining: number | null;
}

export interface WaiverLeagueOverview {
  league_id: string;
  league_name: string;
  league_avatar: string | null;

  roster_id: number;

  roster_size: number;
  roster_capacity: number;
  roster_spots_available: number;

  faab_budget: number;
  faab_used: number;
  faab_remaining: number;
  faab_percent_remaining: number;

  available_player_count: number;

  value_basis: ValueBasis;
  value_label: string;

  suggested_add: PlayerValue | null;
  suggested_drop: PlayerValue | null;

  suggested_add_value: number | null;
  suggested_drop_value: number | null;
  value_gain: number | null;

  can_submit_claim: boolean;
}

export interface WaiverOverviewResponse {
  sleeper_username: string | null;
  leagues: WaiverLeagueOverview[];
}

export interface WaiverClaimRequest {
  league_id: string;
  roster_id: number;

  add_player_id: string;
  drop_player_id: string | null;

  bid: number;
}

export interface WaiverClaimResponse {
  transaction_id: string;
}

export interface WaiverLeagueOption {
  league_id: string;
  league_name: string;
  league_avatar: string | null;

  roster_id: number;

  roster_size: number;
  roster_capacity: number;
  roster_spots_available: number;

  faab_remaining: number;
  faab_percent_remaining: number;
}

export interface WaiverAvailablePlayer extends PlayerValue {
  selected_value: number | null;
}

export interface WaiverAvailablePlayersResponse {
  league_id: string;
  league_name: string;
  league_avatar: string | null;

  roster_id: number;

  value_basis: ValueBasis;
  value_label: string;

  total_players: number;

  players: WaiverAvailablePlayer[];
}

export interface WaiverRosterPlayer extends PlayerValue {
  selected_value: number | null;
}

export interface WaiverRosterPlayersResponse {
  league_id: string;
  league_name: string;

  roster_id: number;

  value_basis: ValueBasis;
  value_label: string;

  total_players: number;

  players: WaiverRosterPlayer[];
}

export interface BulkWaiverPlayerSearchResult {
  player_id: string;

  name: string;
  position: string | null;
  team: string | null;
  age: number | null;

  ktc_value: number | null;
  fc_value: number | null;

  underdog_position_rank: string | null;
}

export interface BulkWaiverLeagueAvailability {
  league_id: string;
  league_name: string;
  league_avatar: string | null;

  roster_id: number;

  is_available: boolean;
  already_rostered_by_you: boolean;
  unavailable_reason: string | null;

  can_submit_claim: boolean;
  claim_blocked_reason: string | null;

  faab_remaining: number;
  roster_spots_available: number;
  requires_drop: boolean;

  add_selected_value: number | null;

  recommended_drop: PlayerValue | null;
  recommended_drop_selected_value: number | null;
}

export interface BulkWaiverAvailabilityResponse {
  player: BulkWaiverPlayerSearchResult;

  value_basis: ValueBasis;
  value_label: string;

  leagues: BulkWaiverLeagueAvailability[];
}

export interface BulkWaiverClaimRequest {
  claims: WaiverClaimRequest[];
}

export interface BulkWaiverClaimResult {
  league_id: string;
  roster_id: number;

  success: boolean;

  transaction_id: string | null;
  error: string | null;
}

export interface BulkWaiverClaimResponse {
  results: BulkWaiverClaimResult[];
}

export type TradeDirection = 'buy' | 'sell';

export interface BulkTradePlayerSearchResult {
  player_id: string;
  name: string;
  position: string | null;
  team: string | null;
  age: number | null;
  ktc_value: number | null;
  fc_value: number | null;
  underdog_position_rank: string | null;
}

export interface TradeDraftPickAsset {
  season: string;
  round: number;
  og_roster_id: number;
  current_owner_roster_id: number;
  original_owner_name: string | null;
  label: string;
}

export interface BulkTradeCounterparty {
  roster_id: number;
  user_id: string | null;
  name: string;
  matching_picks: TradeDraftPickAsset[];
}

export interface BulkTradeLeagueAvailability {
  league_id: string;
  league_name: string;
  league_avatar: string | null;

  your_roster_id: number;

  target_owner_roster_id: number | null;
  target_owner_user_id: string | null;
  target_owner_name: string | null;

  you_own_target_player: boolean;

  is_eligible: boolean;
  ineligibility_reason: string | null;

  matching_picks: TradeDraftPickAsset[];
  counterparty_options: BulkTradeCounterparty[];
}

export interface BulkTradeAvailabilityResponse {
  player: BulkTradePlayerSearchResult;
  direction: TradeDirection;
  pick_season: string;
  pick_round: number;
  leagues: BulkTradeLeagueAvailability[];
}

export interface BulkTradePickReference {
  season: string;
  round: number;
  og_roster_id: number;
}

export interface BulkTradeOfferRequest {
  league_id: string;
  your_roster_id: number;
  counterparty_roster_id: number;
  target_player_id: string;
  direction: TradeDirection;
  pick: BulkTradePickReference;
  expires_at?: number | null;
}

export interface BulkTradeProposalRequest {
  offers: BulkTradeOfferRequest[];
}

export interface BulkTradeProposalResult {
  league_id: string;
  success: boolean;
  transaction_id: string | null;
  error: string | null;
}

export interface BulkTradeProposalResponse {
  results: BulkTradeProposalResult[];
}
