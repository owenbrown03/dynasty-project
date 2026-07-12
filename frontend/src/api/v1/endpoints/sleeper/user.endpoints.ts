import { type AxiosInstance } from 'axios';

import {
  type CommissionerLeagueDuesUpdate,
  type CommissionerLeagueNoteUpdate,
  type CommissionerLeagueSettingsUpdate,
  type CommissionerOrphansResponse,
  type CommissionerWorkspaceResponse,
  type FinanceLeagueSeasonUpdate,
  type FinanceSummaryResponse,
  type Orphan,
  type ReminderCreate,
  type ReminderDelete,
  type ReminderListResponse,
  type ReminderTestSendResponse,
  type ReminderUpdate,
  type Roster,
  type ValueBasis,
} from '@/types';

export const userEndpoints = (client: AxiosInstance, prefix: string) => ({
  sync: (username: string) => client.post(`${prefix}/${username}/sync`),
  getRosters: (username: string) => client.get<Roster[]>(`${prefix}/${username}/rosters`),
  getOrphans: (username: string) => client.get<Orphan[]>(`${prefix}/${username}/orphans`),
  getCommissionerOrphans: (
    username: string,
    valueBasis: ValueBasis,
  ) => client.get<CommissionerOrphansResponse>(
    `${prefix}/${username}/commissioner/orphans`,
    {
      params: {
        value_basis: valueBasis,
      },
    },
  ),
  getCommissionerWorkspace: () => client.get<CommissionerWorkspaceResponse>(
    `${prefix}/commissioner/workspace`,
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
  getFinanceSummary: () => client.get<FinanceSummaryResponse>(
    `${prefix}/finance/summary`,
  ),
  saveFinanceSeason: (
    body: FinanceLeagueSeasonUpdate,
  ) => client.post(
    `${prefix}/finance/season`,
    body,
  ),
  getReminders: () => client.get<ReminderListResponse>(
    `${prefix}/reminders`,
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
  testSendReminder: (
    body: ReminderDelete,
  ) => client.post<ReminderTestSendResponse>(
    `${prefix}/reminders/test-send`,
    body,
  ),
});
