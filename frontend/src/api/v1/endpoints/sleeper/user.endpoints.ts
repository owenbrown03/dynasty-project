import { type AxiosInstance } from 'axios';

import {
  type CommissionerLeagueDuesUpdate,
  type CommissionerLeagueNoteUpdate,
  type CommissionerLeagueSettingsUpdate,
  type CommissionerOrphansResponse,
  type CommissionerWorkspaceResponse,
  type FinanceDefaultsUpdate,
  type FinanceLeagueDefaultsUpdate,
  type FinanceLeagueSeasonUpdate,
  type FinanceSeasonReset,
  type FinanceSummaryResponse,
  type Orphan,
  type ReminderCreate,
  type ReminderDelete,
  type ReminderListResponse,
  type ReminderTestSendResponse,
  type ReminderUpdate,
  type Roster,
  type ValueBasis,
  type CommissionerCutdownLeague,
  type CommissionerCutdownActionRequest,
  type CommissionerCutdownActionResponse,
} from '@/types';

export const userEndpoints = (client: AxiosInstance, prefix: string) => ({
  sync: (username: string) => client.post(`${prefix}/${username}/sync`),
  getRosters: (username: string, signal?: AbortSignal) =>
    client.get<Roster[]>(
      `${prefix}/${username}/rosters`,
      { signal },
    ),
  getOrphans: (username: string, signal?: AbortSignal) =>
    client.get<Orphan[]>(
      `${prefix}/${username}/orphans`,
      { signal },
    ),
  getCommissionerOrphans: (
    username: string,
    valueBasis: ValueBasis,
    signal?: AbortSignal,
  ) => client.get<CommissionerOrphansResponse>(
    `${prefix}/${username}/commissioner/orphans`,
    {
      params: {
        value_basis: valueBasis,
      },
      signal,
    },
  ),
  getCommissionerWorkspace: (signal?: AbortSignal) =>
    client.get<CommissionerWorkspaceResponse>(
      `${prefix}/commissioner/workspace`,
      { signal },
    ),
  saveCommissionerNote: (
    body: CommissionerLeagueNoteUpdate,
  ) => client.post(
    `${prefix}/commissioner/workspace/note`,
    body,
  ),
  saveCommissionerDues: (
    body: CommissionerLeagueDuesUpdate,
  ) => client.post(
    `${prefix}/commissioner/workspace/dues`,
    body,
  ),
  saveCommissionerSettings: (
    body: CommissionerLeagueSettingsUpdate,
  ) => client.post(
    `${prefix}/commissioner/workspace/settings`,
    body,
  ),
  getFinanceSummary: (signal?: AbortSignal) =>
    client.get<FinanceSummaryResponse>(
      `${prefix}/finance/summary`,
      { signal },
    ),
  saveFinanceDefaults: (
    body: FinanceDefaultsUpdate,
  ) => client.post<FinanceSummaryResponse>(
    `${prefix}/finance/defaults`,
    body,
  ),
  saveFinanceLeagueDefaults: (
    body: FinanceLeagueDefaultsUpdate,
  ) => client.post<FinanceSummaryResponse>(
    `${prefix}/finance/defaults/leagues`,
    body,
  ),
  saveFinanceSeason: (
    body: FinanceLeagueSeasonUpdate,
  ) => client.post(
    `${prefix}/finance/season`,
    body,
  ),
  resetFinanceSeason: (
    body: FinanceSeasonReset,
  ) => client.post(
    `${prefix}/finance/season/reset`,
    body,
  ),
  getReminders: (signal?: AbortSignal) =>
    client.get<ReminderListResponse>(
      `${prefix}/reminders`,
      { signal },
    ),
  createReminder: (
    body: ReminderCreate,
  ) => client.post(
    `${prefix}/reminders`,
    body,
  ),
  saveReminder: (
    body: ReminderUpdate,
  ) => client.post(
    `${prefix}/reminders/update`,
    body,
  ),
  deleteReminder: (
    body: ReminderDelete,
  ) => client.post(
    `${prefix}/reminders/delete`,
    body,
  ),
  getCommissionerCutdowns: (signal?: AbortSignal) =>
    client.get<CommissionerCutdownLeague[]>(
      `${prefix}/commissioner/cutdowns`,
      { signal },
    ),
  executeCommissionerCutdownAction: (
    body: CommissionerCutdownActionRequest,
  ) => client.post<CommissionerCutdownActionResponse>(
    `${prefix}/commissioner/cutdowns/action`,
    body,
  ),

  testSendReminder: (
    body: ReminderDelete,
  ) => client.post<ReminderTestSendResponse>(
    `${prefix}/reminders/test-send`,
    body,
  ),
});
