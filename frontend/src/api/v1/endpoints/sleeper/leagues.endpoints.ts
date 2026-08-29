import { type AxiosInstance } from 'axios';

import type {
  LeagueOverview,
  LeagueSelectorItem,
  LeagueDetails,
  Dashboard,
  LeagueFocusItem,
  LeagueFocusUpdate,
  LeagueVisibilityItem,
  LeagueVisibilityUpdate,
  UserLeagueNoteUpdate,
  UserLeagueNoteResponse,
  AuctionDraftCenter,
  ValueBasis,
  RookieWarHistory,
} from '@/types';

export const leaguesEndpoints = (
  client: AxiosInstance,
  prefix: string
) => ({

  getOverview: (
    username: string,
    includeHidden = false,
    signal?: AbortSignal,
  ) =>
    client.get<LeagueOverview[]>(
      `${prefix}/overview/${username}`,
      {
        params: {
          include_hidden: includeHidden,
        },
        signal,
      },
    ),

  getSelector: (
    username: string,
    includeHidden = false,
    signal?: AbortSignal,
  ) =>
    client.get<LeagueSelectorItem[]>(
      `${prefix}/selector/${username}`,
      {
        params: {
          include_hidden: includeHidden,
        },
        signal,
      },
    ),


  getDetails: (
    league_id: string,
    cheap = false,
    signal?: AbortSignal,
  ) =>
    client.get<LeagueDetails>(
      `${prefix}/details/${league_id}`,
      {
        params: { cheap },
        signal,
      },
    ),


  getDashboard: (
    username: string,
    cheap = false,
    signal?: AbortSignal,
  ) =>
    client.get<Dashboard>(
      `${prefix}/dashboard/${username}`,
      {
        params: { cheap },
        signal,
      },
    ),

  setVisibility: (
    leagueId: string,
    payload: LeagueVisibilityUpdate,
  ) =>
    client.put<LeagueVisibilityItem>(
      `${prefix}/visibility/${leagueId}`,
      payload,
    ),
  setFocus: (
    leagueId: string,
    payload: LeagueFocusUpdate,
  ) =>
    client.put<LeagueFocusItem>(
      `${prefix}/focus/${leagueId}`,
      payload,
    ),
  saveNote: (
    payload: UserLeagueNoteUpdate,
  ) =>
    client.post<UserLeagueNoteResponse>(
      `${prefix}/note`,
      payload,
    ),
  getAuctionCenter: (
    draftId: string,
    valueBasis: ValueBasis,
    search: string,
    page: number,
    pageSize: number,
    signal?: AbortSignal,
  ) =>
    client.get<AuctionDraftCenter>(
      `/sleeper/drafts/auction-center`,
      {
        params: {
          draft_id: draftId,
          value_basis: valueBasis,
          search: search || undefined,
          page,
          page_size: pageSize,
        },
        signal,
      },
    ),

  getRookieWarHistory: (
    leagueId?: string,
    rounds?: string,
    signal?: AbortSignal,
  ) =>
    client.get<RookieWarHistory>(
      `/sleeper/drafts/rookie-war/history`,
      {
        params: {
          league_id: leagueId || undefined,
          rounds: rounds || undefined,
        },
        signal,
      },
    ),
});
