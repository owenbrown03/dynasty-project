import type { ValueBasis } from '@/types';

export const queryKeys = {
  bootstrap: ['bootstrap'] as const,

  adp: {
    results: (filters: Record<string, unknown>) =>
      ['adp-results', filters] as const,
    metadata: (filters: Record<string, unknown>) =>
      ['adp-metadata', filters] as const,
    report: ['adp-report'] as const,
  },

  users: {
    rosters: (
      username: string | null | undefined,
    ) => ['rosters', username ?? null] as const,
    orphans: (
      username: string | null | undefined,
    ) => ['orphans', username ?? null] as const,
    commissionerOrphans: (
      username: string | null | undefined,
      valueBasis: ValueBasis,
    ) =>
      [
        'commissioner-orphans',
        username ?? null,
        valueBasis,
      ] as const,
    commissionerWorkspace: ['commissioner-workspace'] as const,
    financeSummary: ['finance-summary'] as const,
    reminders: ['reminders'] as const,
  },

  leagues: {
    detailsRoot: ['league-details'] as const,
    overviewRoot: ['league-overview'] as const,
    overview: (
      username: string | null | undefined,
      includeHidden = false,
    ) =>
      [
        'league-overview',
        username ?? null,
        includeHidden,
      ] as const,
    details: (
      leagueId: string | undefined,
      viewerKey: string | null | undefined,
      cheap = false,
    ) =>
      [
        'league-details',
        leagueId ?? null,
        viewerKey ?? null,
        cheap,
      ] as const,
    dashboard: (
      username: string | null | undefined,
      cheap = false,
    ) =>
      ['league-dashboard', username ?? null, cheap] as const,
  },

  drafts: {
    auctionCenter: (
      draftId: string | null | undefined,
      valueBasis: ValueBasis,
      search: string,
      page: number,
      pageSize: number,
    ) =>
      [
        'auction-draft-center',
        draftId ?? null,
        valueBasis,
        search,
        page,
        pageSize,
      ] as const,
  },

  advisor: {
    recommendations: (
      username: string | null | undefined,
      leagueId?: string | null,
    ) => [
      'advisor-recommendations',
      username ?? null,
      leagueId ?? null,
    ] as const,
    directives: (
      username: string | null | undefined,
    ) => [
      'advisor-directives',
      username ?? null,
    ] as const,
    cachedRecommendations: (
      username: string | null | undefined,
      leagueId?: string | null,
    ) => [
      'advisor-cached-recommendations',
      username ?? null,
      leagueId ?? null,
    ] as const,
    digest: (
      username: string | null | undefined,
    ) => ['advisor-digest', username ?? null] as const,
  },

  trades: {
    signals: (
      username: string | null | undefined,
      cheap = false,
    ) => ['trade-signals', username ?? null, cheap] as const,
    bulkPlayerSearch: (query: string) =>
      ['bulk-trade-player-search', query] as const,
    bulkAvailability: (
      username: string | null | undefined,
      packageKey: string,
    ) =>
      [
        'bulk-trade-availability',
        username ?? null,
        packageKey,
      ] as const,
    bulkAvailabilityRoot: [
      'bulk-trade-availability',
    ] as const,
  },

  waivers: {
    overview: (
      username: string | null | undefined,
      valueBasis: ValueBasis,
      cheap = false,
    ) =>
      [
        'waiver-overview',
        username ?? null,
        valueBasis,
        cheap,
      ] as const,
    overviewRoot: ['waiver-overview'] as const,
    recentDrops: (
      username: string | null | undefined,
      valueBasis: ValueBasis,
      page: number,
      pageSize: number,
      sortBy: 'value' | 'recency',
      cheap = false,
    ) =>
      [
        'waiver-recent-drops',
        username ?? null,
        valueBasis,
        page,
        pageSize,
        sortBy,
        cheap,
      ] as const,
    recentDropsRoot: ['waiver-recent-drops'] as const,
    leagues: (
      username: string | null | undefined,
    ) => ['waiver-leagues', username ?? null] as const,
    leaguesRoot: ['waiver-leagues'] as const,
    availablePlayers: (
      username: string | null | undefined,
      leagueId: string | undefined,
      valueBasis: ValueBasis,
      page: number,
      pageSize: number,
    ) =>
      [
        'waiver-available-players',
        username ?? null,
        leagueId ?? 'all',
        valueBasis,
        page,
        pageSize,
      ] as const,
    availablePlayersRoot: [
      'waiver-available-players',
    ] as const,
    rosterPlayers: (
      username: string | null | undefined,
      leagueId: string | undefined,
      valueBasis: ValueBasis,
    ) =>
      [
        'waiver-roster-players',
        username ?? null,
        leagueId ?? null,
        valueBasis,
      ] as const,
    rosterPlayersRoot: [
      'waiver-roster-players',
    ] as const,
    bulkPlayerSearch: (query: string) =>
      ['bulk-waiver-player-search', query] as const,
    bulkAvailability: (
      username: string | null | undefined,
      playerId: string | undefined,
      valueBasis: ValueBasis,
    ) =>
      [
        'bulk-waiver-availability',
        username ?? null,
        playerId ?? null,
        valueBasis,
      ] as const,
    bulkAvailabilityRoot: [
      'bulk-waiver-availability',
    ] as const,
  },

  players: {
    tiers: (
      valueBasis: ValueBasis,
      leagueId?: string,
      viewerKey?: string | null,
      cheap = false,
    ) =>
      [
        'player-tiers',
        valueBasis,
        leagueId ?? null,
        viewerKey ?? null,
        cheap,
      ] as const,
    personalSearch: (query: string) =>
      ['personal-values-search', query] as const,
    personalDetail: (
      leagueId: string | undefined,
      playerId: string | undefined,
    ) =>
      [
        'personal-values-detail',
        leagueId ?? null,
        playerId ?? null,
      ] as const,
    personalDetailRoot: ['personal-values-detail'] as const,
    personalRankings: (
      leagueId: string | undefined,
      position: string,
      scope: string,
    ) =>
      [
        'personal-values-rankings',
        leagueId ?? null,
        position,
        scope,
      ] as const,
  },
} as const;

export const BOOTSTRAP_QUERY_KEY =
  queryKeys.bootstrap;
