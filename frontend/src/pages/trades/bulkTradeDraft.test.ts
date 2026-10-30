import { describe, expect, it, beforeEach } from 'vitest';
import {
  BULK_TRADE_DRAFT_STORAGE_KEY,
  clearBulkTradeDraft,
  loadBulkTradeDraft,
  reconcileLeagueSelections,
  saveBulkTradeDraft,
  type BulkTradeDraftData,
} from './bulkTradeDraft';
import type { BulkTradeLeagueAvailability } from '@/types';

describe('bulkTradeDraft', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('returns null when no draft is stored', () => {
    expect(loadBulkTradeDraft()).toBeNull();
  });

  it('saves and loads draft data to and from localStorage', () => {
    const draft: BulkTradeDraftData = {
      sendPlayers: [
        {
          player_id: '123',
          name: 'Player One',
          position: 'WR',
          team: 'DAL',
          age: 25,
          ktc_value: 5000,
          fc_value: 5000,
          underdog_position_rank: null,
        },
      ],
      sendPicks: [{ season: '2027', round: 1 }],
      receivePlayers: [],
      receivePicks: [{ season: '2027', round: 2 }],
      defaultSendFaab: 10,
      defaultReceiveFaab: 0,
      selectionsByLeagueId: {
        'league-1': {
          selected: true,
          counterparties: {
            2: {
              selected: true,
              sendPickOgRosterIdsByRequestIndex: { 0: 1 },
              receivePickOgRosterIdsByRequestIndex: { 0: 2 },
              sendFaab: 10,
              receiveFaab: 0,
            },
          },
        },
      },
      updatedAt: 123456789,
    };

    saveBulkTradeDraft(draft);
    const loaded = loadBulkTradeDraft();
    expect(loaded).toEqual(draft);
  });

  it('clears draft from localStorage', () => {
    saveBulkTradeDraft({
      sendPlayers: [],
      sendPicks: [],
      receivePlayers: [],
      receivePicks: [],
      defaultSendFaab: 0,
      defaultReceiveFaab: 0,
      selectionsByLeagueId: {},
      updatedAt: 1,
    });
    expect(window.localStorage.getItem(BULK_TRADE_DRAFT_STORAGE_KEY)).not.toBeNull();

    clearBulkTradeDraft();
    expect(window.localStorage.getItem(BULK_TRADE_DRAFT_STORAGE_KEY)).toBeNull();
    expect(loadBulkTradeDraft()).toBeNull();
  });

  it('reconciles incoming availability leagues with existing selections without resetting custom user choices', () => {
    const leagues: BulkTradeLeagueAvailability[] = [
      {
        league_id: 'league-1',
        league_name: 'League 1',
        league_avatar: null,
        your_roster_id: 1,
        your_faab_available: 100,
        is_eligible: true,
        ineligibility_reason: null,
        counterparty_options: [
          {
            roster_id: 2,
            user_id: 'user-2',
            name: 'User 2',
            faab_available: 50,
            send_pick_choices: [],
            receive_pick_choices: [],
          },
          {
            roster_id: 3,
            user_id: 'user-3',
            name: 'User 3',
            faab_available: 50,
            send_pick_choices: [],
            receive_pick_choices: [],
          },
        ],
      },
    ];

    // User previously unchecked league-1, and customized manager 2
    const currentSelections = {
      'league-1': {
        selected: false,
        counterparties: {
          2: {
            selected: false,
            sendPickOgRosterIdsByRequestIndex: {},
            receivePickOgRosterIdsByRequestIndex: {},
            sendFaab: 25,
            receiveFaab: 5,
          },
        },
      },
    };

    const reconciled = reconcileLeagueSelections(leagues, currentSelections, 0, 0);

    // League selected state should be preserved as false
    expect(reconciled['league-1'].selected).toBe(false);
    // Counterparty 2 custom state preserved
    expect(reconciled['league-1'].counterparties[2]).toEqual({
      selected: false,
      sendPickOgRosterIdsByRequestIndex: {},
      receivePickOgRosterIdsByRequestIndex: {},
      sendFaab: 25,
      receiveFaab: 5,
    });
    // Newly appeared counterparty 3 initialized with defaults
    expect(reconciled['league-1'].counterparties[3]).toBeDefined();
    expect(reconciled['league-1'].counterparties[3].selected).toBe(true);
  });
});
