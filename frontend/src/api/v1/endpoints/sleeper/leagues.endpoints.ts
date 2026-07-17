import { type AxiosInstance } from 'axios';

import type {
  LeagueOverview,
  LeagueDetails,
  Dashboard,
  LeagueVisibilityItem,
  LeagueVisibilityUpdate,
  UserLeagueNoteUpdate,
  UserLeagueNoteResponse,
  AuctionDraftCenter,
  ValueBasis,
} from '@/types';

export const leaguesEndpoints = (
  client: AxiosInstance,
  prefix: string
) => ({

  getOverview: (
    username: string,
    includeHidden = false,
  ) =>
    client.get<LeagueOverview[]>(
      `${prefix}/overview/${username}`,
      {
        params: {
          include_hidden: includeHidden,
        },
      },
    ),


  getDetails: (
    league_id: string
  ) =>
    client.get<LeagueDetails>(
      `${prefix}/details/${league_id}`
    ),


  getDashboard: (
    username: string
  ) =>
    client.get<Dashboard>(
      `${prefix}/dashboard/${username}`
    ),

  setVisibility: (
    leagueId: string,
    payload: LeagueVisibilityUpdate,
  ) =>
    client.put<LeagueVisibilityItem>(
      `${prefix}/visibility/${leagueId}`,
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
      },
    ),
});
