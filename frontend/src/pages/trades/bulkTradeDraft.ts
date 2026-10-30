import type {
  BulkTradeCounterpartySelection,
  BulkTradeLeagueSelection,
} from './BulkTradeLeagueRow';
import {
  createCounterpartySelection,
  createLeagueSelection,
} from './BulkTradeLeagueRow';
import type {
  BulkTradeLeagueAvailability,
  BulkTradePickRequest,
  BulkTradePlayerSearchResult,
} from '@/types';

export const BULK_TRADE_DRAFT_STORAGE_KEY = 'bulk_trade_draft_v1';

export interface BulkTradeDraftData {
  sendPlayers: BulkTradePlayerSearchResult[];
  sendPicks: BulkTradePickRequest[];
  receivePlayers: BulkTradePlayerSearchResult[];
  receivePicks: BulkTradePickRequest[];
  defaultSendFaab: number;
  defaultReceiveFaab: number;
  selectionsByLeagueId: Record<string, BulkTradeLeagueSelection>;
  updatedAt: number;
}

export function loadBulkTradeDraft(): BulkTradeDraftData | null {
  if (typeof window === 'undefined' || !window.localStorage) {
    return null;
  }

  try {
    const raw = window.localStorage.getItem(BULK_TRADE_DRAFT_STORAGE_KEY);
    if (!raw) {
      return null;
    }

    const data = JSON.parse(raw);
    if (
      data &&
      typeof data === 'object' &&
      Array.isArray(data.sendPlayers) &&
      Array.isArray(data.sendPicks) &&
      Array.isArray(data.receivePlayers) &&
      Array.isArray(data.receivePicks)
    ) {
      return {
        sendPlayers: data.sendPlayers,
        sendPicks: data.sendPicks,
        receivePlayers: data.receivePlayers,
        receivePicks: data.receivePicks,
        defaultSendFaab: typeof data.defaultSendFaab === 'number' ? data.defaultSendFaab : 0,
        defaultReceiveFaab: typeof data.defaultReceiveFaab === 'number' ? data.defaultReceiveFaab : 0,
        selectionsByLeagueId:
          data.selectionsByLeagueId && typeof data.selectionsByLeagueId === 'object'
            ? data.selectionsByLeagueId
            : {},
        updatedAt: typeof data.updatedAt === 'number' ? data.updatedAt : Date.now(),
      };
    }
  } catch {
    // Ignore parse or storage errors in private mode
  }

  return null;
}

export function saveBulkTradeDraft(draft: BulkTradeDraftData | null): void {
  if (typeof window === 'undefined' || !window.localStorage) {
    return;
  }

  try {
    if (!draft) {
      window.localStorage.removeItem(BULK_TRADE_DRAFT_STORAGE_KEY);
      return;
    }

    window.localStorage.setItem(
      BULK_TRADE_DRAFT_STORAGE_KEY,
      JSON.stringify(draft),
    );
  } catch {
    // Ignore quota or permission errors
  }
}

export function clearBulkTradeDraft(): void {
  saveBulkTradeDraft(null);
}

/**
 * Reconciles incoming availability leagues with existing selections.
 * Preserves user-customized selections (checked status, picked pick assets, custom FAAB)
 * and only generates default selections for newly discovered leagues/counterparties.
 */
export function reconcileLeagueSelections(
  leagues: BulkTradeLeagueAvailability[],
  currentSelections: Record<string, BulkTradeLeagueSelection>,
  defaultSendFaab = 0,
  defaultReceiveFaab = 0,
): Record<string, BulkTradeLeagueSelection> {
  const next: Record<string, BulkTradeLeagueSelection> = {};

  for (const league of leagues) {
    const existingLeague = currentSelections[league.league_id];

    if (!existingLeague) {
      next[league.league_id] = createLeagueSelection(
        league,
        defaultSendFaab,
        defaultReceiveFaab,
      );
      continue;
    }

    // Preserve existing league selection and counterparty choices
    const counterparties: Record<number, BulkTradeCounterpartySelection> = {};

    for (const cp of league.counterparty_options) {
      const existingCp = existingLeague.counterparties[cp.roster_id];
      if (existingCp) {
        counterparties[cp.roster_id] = existingCp;
      } else {
        counterparties[cp.roster_id] = createCounterpartySelection(
          cp,
          defaultSendFaab,
          defaultReceiveFaab,
        );
      }
    }

    next[league.league_id] = {
      selected: existingLeague.selected,
      counterparties,
    };
  }

  return next;
}
