export interface Movement {
  name: string;
  signal: string;
}

export interface UserMovements {
  display_name: string;
  avatar: string | null;
  adds: Movement[];
  drops: Movement[];
}

export interface Transaction {
  transaction_id: string;
  league_name: string;
  league_avatar: string | null;
  league_settings: string[];
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

export interface EmailVerificationRequestResponse {
  email_verified: boolean;
  verification_email_sent_at: string | null;
  delivery: 'smtp' | 'log';
  verification_url: string | null;
}

export interface EmailVerificationConfirmRequest {
  token: string;
}

export interface EmailVerificationStatusResponse {
  email_verified: boolean;
  verification_email_sent_at: string | null;
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
  email_verified: boolean;
  verification_email_sent_at: string | null;
}

export interface BootstrapSleeper {
  linked: boolean;
  sleeper_username: string | null;
  sleeper_user_id: string | null;
  sleeper_avatar: string | null;
  can_read: boolean;
  can_write: boolean;
}

export interface SleeperConnection {
  linked: boolean;
  sleeper_username: string | null;
  sleeper_user_id: string | null;
  sleeper_avatar: string | null;
  can_read: boolean;
  can_write: boolean;
}

export interface Bootstrap {
  authenticated: boolean;
  site_user: BootstrapUser | null;
  sleeper: BootstrapSleeper;
  theme_preference: ThemePreference | null;
  accent_color: AccentColor | null;
  value_preference: ValueBasis | null;
  war_value_settings: WarValueSettings;
  draft_pick_projection_settings: DraftPickProjectionSettings;
}

export type ThemePreference =
  | 'light'
  | 'dark'
  | 'system';

export type AccentColor =
  | 'blue'
  | 'green'
  | 'purple'
  | 'red'
  | 'orange'
  | 'teal'
  | 'pink';

export type WarValueTimeframe =
  | 'redraft'
  | 'dynasty';

export type WarValueScope =
  | 'starter'
  | 'roster';

export interface WarValueConfig {
  timeframe: WarValueTimeframe;
  scope: WarValueScope;
}

export interface WarValueSettings {
  sleeper_projection: WarValueConfig;
  my: WarValueConfig;
}

export type DraftPickProjectionMethod =
  | 'reverse_standings'
  | 'max_pf'
  | 'redraft_starter_war'
  | 'redraft_roster_war';

export type DraftPickProjectionPhaseMethod =
  | 'none'
  | DraftPickProjectionMethod;

export interface DraftPickProjectionSettings {
  enabled: boolean;
  switch_week: number;
  before_week_method: DraftPickProjectionPhaseMethod;
  from_week_method: DraftPickProjectionMethod;
}

export interface LeagueOverview {
  league_id: string;
  league_name: string;
  avatar: string | null;
  season: string | null;
  total_rosters: number | null;
  is_hidden: boolean;
}

export interface LeagueVisibilityUpdate {
  hidden: boolean;
}

export interface LeagueVisibilityItem {
  league_id: string;
  hidden: boolean;
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

export interface LeagueWarPositionValue {
  position: string;
  war: number;
}

export interface LeagueWarPositionSeason {
  season: string;
  source: string;
  values: LeagueWarPositionValue[];
}

export interface LeagueWarPlayerPoint {
  player_id: string;
  name: string;
  position: string;
  war: number;
  rank: number;
}

export interface LeagueWarPlayerSeason {
  season: string;
  source: string;
  war_type: string;
  players: LeagueWarPlayerPoint[];
}

export interface LeaguePick {
  season: string;
  round: number;
  og_roster_id: number;
  current_owner_roster_id: number;
  label: string;
  slot: number | null;
  projected_slot: number | null;
  slot_source_label: string | null;
  fc_value: number | null;
  ktc_value: number | null;
  rookie_war_value: number | null;
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
  adp_value?: number | null;
  fc_trend_30_day: number | null;

  redraft_starter_war: number | null;
  redraft_roster_war: number | null;
  dynasty_starter_war: number | null;
  dynasty_roster_war: number | null;
  my_redraft_starter_war?: number | null;
  my_redraft_roster_war?: number | null;
  my_dynasty_starter_war?: number | null;
  my_dynasty_roster_war?: number | null;
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
  total_trades: number;
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
  total_pick_rookie_war_value: number;
  total_asset_ktc_value: number;
  total_asset_fc_value: number;
  stat_ranks: Record<string, number>;

  rank: number;

  players: LeaguePlayer[];
  picks: LeaguePick[];
}

export interface LeagueRosterConstructionTarget {
  position: string;
  target_count: number;
  war_share: number;
}

export interface LeagueDetails {
  league_id: string;
  league_name: string;
  avatar: string | null;
  season: string;
  total_rosters: number;
  roster_positions: string[];
  roster_construction_targets: LeagueRosterConstructionTarget[];
  note: string;
  draft_pick_projection_summary: string | null;
  settings_badges: string[];
  settings_details: LeagueSettingsDetail[];
  war_position_history: LeagueWarPositionSeason[];
  war_player_history: LeagueWarPlayerSeason[];
  rosters: LeagueRoster[];
}

export interface DashboardLeague {
  league_id: string;
  league_name: string;
  avatar: string | null;
  league_size: number;
  wins: number;
  losses: number;
  ties: number;

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

export interface Dashboard {
  leagues: DashboardLeague[];
}

export type ValueBasis =
  | 'ktc'
  | 'fantasycalc'
  | 'adp'
  | 'sleeper_war'
  | 'my_war'
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

export interface PersonalValueSearchResult {
  player_id: string;
  name: string;
  position: string | null;
  team: string | null;
  age: number | null;
  underdog_position_rank: string | null;
  ktc_value: number | null;
  fc_value: number | null;
  adp_value?: number | null;
  dynasty_roster_war: number | null;
}

export interface PersonalProjectionOutcomeItem {
  position_rank: number;
  probability: number;
}

export interface PersonalProjectionSeasonItem {
  season: number;
  outcomes: PersonalProjectionOutcomeItem[];
  default_position_rank: number | null;
  is_customized: boolean;
}

export interface PersonalValueMetrics {
  redraft_starter_war: number | null;
  redraft_roster_war: number | null;
  dynasty_starter_war: number | null;
  dynasty_roster_war: number | null;
}

export interface PersonalValuePlayer {
  player_id: string;
  name: string;
  position: string;
  team: string | null;
  age: number | null;
  underdog_position_rank: string | null;
  ktc_value: number | null;
  fc_value: number | null;
  adp_value?: number | null;
}

export interface PersonalValueLeagueContext {
  league_id: string;
  league_name: string;
  season: number;
  total_rosters: number;
}

export interface PersonalValueDetail {
  context: PersonalValueLeagueContext;
  player: PersonalValuePlayer;
  market_values: PersonalValueMetrics;
  custom_values: PersonalValueMetrics;
  delta_values: PersonalValueMetrics;
  seasons: PersonalProjectionSeasonItem[];
}

export interface PersonalValuePoolItem {
  player: PersonalValuePlayer;
  market_values: PersonalValueMetrics;
  custom_values: PersonalValueMetrics;
  delta_values: PersonalValueMetrics;
  is_customized: boolean;
}

export interface PersonalValuePoolGroup {
  position: string;
  players: PersonalValuePoolItem[];
}

export interface PersonalValuePoolResponse {
  context: PersonalValueLeagueContext;
  groups: PersonalValuePoolGroup[];
}

export interface PersonalProjectionSeasonUpdate {
  season: number;
  outcomes: PersonalProjectionOutcomeItem[];
}

export interface PersonalValueUpdateRequest {
  seasons: PersonalProjectionSeasonUpdate[];
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
  projected_slot: number | null;
  slot_source_label: string | null;
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

export interface CommissionerLeagueDuesEntry {
  league_id: string;
  roster_id: number;
  roster_name: string;
  season: string;
  traded_pick_count: number;
  traded_pick_labels: string[];
  buy_in_amount: number | null;
  is_paid: boolean;
  paid_at: string | null;
}

export interface CommissionerWorkspaceLeague {
  league_id: string;
  league_name: string;
  league_season: string;
  note: string;
  paid_years_ahead: number;
  dues: CommissionerLeagueDuesEntry[];
}

export interface CommissionerWorkspaceResponse {
  leagues: CommissionerWorkspaceLeague[];
}

export interface CommissionerLeagueNoteUpdate {
  league_id: string;
  note: string;
}

export interface UserLeagueNoteUpdate {
  league_id: string;
  note: string;
}

export interface UserLeagueNoteResponse {
  league_id: string;
  note: string;
}


export interface CommissionerLeagueDuesUpdate {
  league_id: string;
  roster_id: number;
  season: string;
  buy_in_amount: number | null;
  is_paid: boolean;
}

export interface CommissionerLeagueSettingsUpdate {
  league_id: string;
  paid_years_ahead: number;
}

export interface FinancePlacePayout {
  place: number;
  amount: number;
}

export interface FinanceLeagueSeasonEntry {
  league_id: string;
  league_family_id: string;
  league_name: string;
  season: string;
  status: string;
  total_rosters: number;
  rank: number | null;
  wins: number | null;
  losses: number | null;
  points_for: number | null;
  finish_place: number | null;
  projected_finish_place: number | null;
  buy_in_amount: number;
  winnings_amount: number;
  payout_structure: FinancePlacePayout[];
  buy_in_source: 'season_override' | 'league_default' | 'global_default' | 'commissioner_dues' | 'none';
  payout_source: 'season_override' | 'league_default' | 'global_default' | 'none';
  has_season_override: boolean;
  has_league_default: boolean;
  is_excluded: boolean;
  projected_winnings_amount: number;
  projected_winnings_source: 'heuristic' | 'historical_rank' | 'configured_place' | 'seed_probability' | 'no_projection';
  net_amount: number;
}

export interface FinanceDefaultSettings {
  buy_in_amount: number | null;
  payout_structure: FinancePlacePayout[];
}

export interface FinanceLeagueDefaultEntry {
  league_family_id: string;
  league_name: string;
  buy_in_amount: number | null;
  payout_structure: FinancePlacePayout[];
}

export interface FinanceSummaryResponse {
  total_buy_ins: number;
  total_winnings: number;
  total_net: number;
  projected_current_winnings: number;
  defaults: FinanceDefaultSettings;
  league_defaults: FinanceLeagueDefaultEntry[];
  seasons: FinanceLeagueSeasonEntry[];
}

export interface FinanceLeagueSeasonUpdate {
  league_id: string;
  season: string;
  buy_in_amount: number;
  payout_structure: FinancePlacePayout[];
  is_excluded: boolean;
}

export interface FinanceSeasonReset {
  league_id: string;
  season: string;
}

export interface FinanceDefaultsUpdate {
  buy_in_amount: number | null;
  payout_structure: FinancePlacePayout[];
}

export interface FinanceLeagueDefaultsUpdate extends FinanceDefaultsUpdate {
  league_family_ids: string[];
}

export interface ReminderItem {
  id: number;
  league_id: string | null;
  title: string;
  note: string;
  due_week: number | null;
  due_season: string | null;
  delivery_channel: string;
  completed: boolean;
  email_sent_at: string | null;
  updated_at: string;
}

export interface ReminderListResponse {
  reminders: ReminderItem[];
}

export interface ReminderCreate {
  league_id: string | null;
  title: string;
  note: string;
  due_week: number | null;
  due_season: string | null;
  delivery_channel: string;
}

export interface ReminderUpdate extends ReminderCreate {
  id: number;
  completed: boolean;
}

export interface ReminderDelete {
  id: number;
}

export interface ReminderTestSendResponse {
  delivery: 'smtp' | 'log';
  recipient: string;
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
  my_redraft_starter_war?: number | null;
  my_redraft_roster_war?: number | null;
  my_dynasty_starter_war?: number | null;
  my_dynasty_roster_war?: number | null;

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

export interface WaiverRecentlyDroppedPlayer extends PlayerValue {
  transaction_id: string;
  dropped_at_ms: number;

  league_id: string;
  league_name: string;
  league_avatar: string | null;

  roster_id: number;

  roster_spots_available: number;
  faab_remaining: number;
  faab_percent_remaining: number;

  can_submit_claim: boolean;
  claim_blocked_reason: string | null;

  selected_value: number | null;
}

export interface WaiverRecentlyDroppedResponse {
  sleeper_username: string | null;

  value_basis: ValueBasis;
  value_label: string;

  sync_requested: boolean;

  page: number;
  page_size: number;
  total_pages: number;
  total_players: number;

  players: WaiverRecentlyDroppedPlayer[];
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

export interface WaiverAvailableLeagueAvailability {
  league_id: string;
  league_name: string;
  league_avatar: string | null;

  roster_id: number;
  roster_size: number;
  roster_capacity: number;
  roster_spots_available: number;

  faab_remaining: number;
  faab_percent_remaining: number;

  can_submit_claim: boolean;
  claim_blocked_reason: string | null;

  selected_value: number | null;
}

export interface WaiverAvailablePlayer extends PlayerValue {
  league_id: string | null;
  league_name: string | null;
  league_avatar: string | null;

  roster_id: number | null;
  roster_size: number | null;
  roster_capacity: number | null;
  roster_spots_available: number | null;

  faab_remaining: number | null;
  faab_percent_remaining: number | null;

  can_submit_claim: boolean;
  claim_blocked_reason: string | null;

  league_count: number;
  league_availability: WaiverAvailableLeagueAvailability[];

  selected_value: number | null;
}

export interface WaiverAvailablePlayersResponse {
  league_id: string | null;
  league_name: string;
  league_avatar: string | null;

  roster_id: number | null;
  is_all_leagues: boolean;

  value_basis: ValueBasis;
  value_label: string;

  page: number;
  page_size: number;
  total_pages: number;
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
  pick_choices: BulkTradePickChoice[];
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

  pick_choices: BulkTradePickChoice[];
  counterparty_options: BulkTradeCounterparty[];
}

export interface BulkTradeAvailabilityResponse {
  direction: TradeDirection;
  players: BulkTradePlayerSearchResult[];
  picks: BulkTradePickRequest[];
  leagues: BulkTradeLeagueAvailability[];
}

export interface BulkTradePickRequest {
  season: string;
  round: number;
}

export interface BulkTradePickChoice {
  request_index: number;
  season: string;
  round: number;
  matching_picks: TradeDraftPickAsset[];
}

export interface BulkTradePickReference {
  season: string;
  round: number;
  og_roster_id: number;
}

export interface BulkTradeAvailabilityRequest {
  direction: TradeDirection;
  player_ids: string[];
  picks: BulkTradePickRequest[];
}

export interface BulkTradeOfferRequest {
  league_id: string;
  your_roster_id: number;
  counterparty_roster_id: number;
  player_ids: string[];
  direction: TradeDirection;
  picks: BulkTradePickReference[];
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

export interface TradeCalculatorPickValueResponse {
  season: string;
  round: number;
  slot: number | null;
  total_rosters: number;
  num_qbs: number;
  ppr: number;
  ktc_value: number | null;
  fc_value: number | null;
  rookie_war_value: number | null;
}
