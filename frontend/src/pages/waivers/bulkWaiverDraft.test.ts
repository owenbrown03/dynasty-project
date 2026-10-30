import { beforeEach, describe, expect, it } from 'vitest';
import {
  BULK_WAIVER_DRAFT_KEY,
  clearBulkWaiverDraft,
  loadBulkWaiverDraft,
  reconcileBulkWaiverClaims,
  saveBulkWaiverDraft,
  type BulkWaiverDraft,
} from './bulkWaiverDraft';
import type {
  BulkWaiverLeagueAvailability,
  BulkWaiverPlayerSearchResult,
  WaiverClaimRequest,
} from '@/types';

const samplePlayer: BulkWaiverPlayerSearchResult = {
  player_id: '1234',
  name: 'Isaiah Likely',
  position: 'TE',
  team: 'BAL',
  age: 24,
  ktc_value: 3500,
  fc_value: 3200,
  underdog_position_rank: 'TE14',
};

const sampleClaim: WaiverClaimRequest = {
  league_id: 'league-1',
  roster_id: 1,
  add_player_id: '1234',
  drop_player_id: '9999',
  bid: 15,
};

describe('bulkWaiverDraft', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('returns null when no draft exists', () => {
    expect(loadBulkWaiverDraft()).toBeNull();
  });

  it('saves and loads a draft successfully', () => {
    const draft: BulkWaiverDraft = {
      selectedPlayer: samplePlayer,
      claimsByLeagueId: { 'league-1': sampleClaim },
      updatedAt: 123456789,
    };

    saveBulkWaiverDraft(draft);
    const loaded = loadBulkWaiverDraft();
    expect(loaded).toEqual(draft);
  });

  it('clears the draft from storage', () => {
    const draft: BulkWaiverDraft = {
      selectedPlayer: samplePlayer,
      claimsByLeagueId: { 'league-1': sampleClaim },
      updatedAt: 123456789,
    };

    saveBulkWaiverDraft(draft);
    expect(localStorage.getItem(BULK_WAIVER_DRAFT_KEY)).not.toBeNull();

    clearBulkWaiverDraft();
    expect(loadBulkWaiverDraft()).toBeNull();
    expect(localStorage.getItem(BULK_WAIVER_DRAFT_KEY)).toBeNull();
  });

  it('reconciles claims keeping only available leagues for the selected player', () => {
    const availableLeagues: BulkWaiverLeagueAvailability[] = [
      {
        league_id: 'league-1',
        league_name: 'Dynasty 1',
        league_avatar: null,
        roster_id: 1,
        is_available: true,
        already_rostered_by_you: false,
        unavailable_reason: null,
        can_submit_claim: true,
        claim_blocked_reason: null,
        faab_remaining: 100,
        roster_spots_available: 1,
        requires_drop: true,
        recommended_drop: null,
        add_selected_value: null,
        recommended_drop_selected_value: null,
      },
      {
        league_id: 'league-2',
        league_name: 'Dynasty 2',
        league_avatar: null,
        roster_id: 2,
        is_available: true,
        already_rostered_by_you: false,
        unavailable_reason: null,
        can_submit_claim: true,
        claim_blocked_reason: null,
        faab_remaining: 85,
        roster_spots_available: 2,
        requires_drop: false,
        recommended_drop: null,
        add_selected_value: null,
        recommended_drop_selected_value: null,
      },
    ];

    const existingClaims: Record<string, WaiverClaimRequest> = {
      'league-1': sampleClaim,
      'league-3': {
        league_id: 'league-3',
        roster_id: 3,
        add_player_id: '1234',
        drop_player_id: null,
        bid: 5,
      },
      'league-2-wrong-player': {
        league_id: 'league-2',
        roster_id: 2,
        add_player_id: '5678', // different player
        drop_player_id: null,
        bid: 10,
      },
    };

    const reconciled = reconcileBulkWaiverClaims(availableLeagues, existingClaims, '1234');
    expect(Object.keys(reconciled)).toEqual(['league-1']);
    expect(reconciled['league-1']).toEqual(sampleClaim);
  });
});
