import type {
  BulkWaiverLeagueAvailability,
  BulkWaiverPlayerSearchResult,
  WaiverClaimRequest,
} from '@/types';

export const BULK_WAIVER_DRAFT_KEY = 'bulk_waiver_draft_v1';

export interface BulkWaiverDraft {
  selectedPlayer: BulkWaiverPlayerSearchResult | undefined;
  claimsByLeagueId: Record<string, WaiverClaimRequest>;
  updatedAt: number;
}

export function loadBulkWaiverDraft(): BulkWaiverDraft | null {
  if (typeof window === 'undefined' || !window.localStorage) {
    return null;
  }

  try {
    const raw = window.localStorage.getItem(BULK_WAIVER_DRAFT_KEY);
    if (!raw) {
      return null;
    }

    const parsed = JSON.parse(raw) as Partial<BulkWaiverDraft>;
    if (!parsed || typeof parsed !== 'object') {
      return null;
    }

    if (!parsed.selectedPlayer || !parsed.claimsByLeagueId) {
      return null;
    }

    return {
      selectedPlayer: parsed.selectedPlayer,
      claimsByLeagueId: parsed.claimsByLeagueId,
      updatedAt: parsed.updatedAt ?? 0,
    };
  } catch {
    return null;
  }
}

export function saveBulkWaiverDraft(draft: BulkWaiverDraft): void {
  if (typeof window === 'undefined' || !window.localStorage) {
    return;
  }

  try {
    window.localStorage.setItem(BULK_WAIVER_DRAFT_KEY, JSON.stringify(draft));
  } catch {
    // Ignore storage quota or disabled storage
  }
}

export function clearBulkWaiverDraft(): void {
  if (typeof window === 'undefined' || !window.localStorage) {
    return;
  }

  try {
    window.localStorage.removeItem(BULK_WAIVER_DRAFT_KEY);
  } catch {
    // Ignore storage issues
  }
}

export function reconcileBulkWaiverClaims(
  availableLeagues: BulkWaiverLeagueAvailability[],
  existingClaims: Record<string, WaiverClaimRequest>,
  selectedPlayerId: string,
): Record<string, WaiverClaimRequest> {
  const availableLeagueIds = new Set(availableLeagues.map((l) => l.league_id));
  const reconciled: Record<string, WaiverClaimRequest> = {};

  for (const [leagueId, claim] of Object.entries(existingClaims)) {
    if (availableLeagueIds.has(leagueId) && claim.add_player_id === selectedPlayerId) {
      reconciled[leagueId] = claim;
    }
  }

  return reconciled;
}
