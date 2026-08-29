import {
  CheckSquare,
  Square,
} from 'lucide-react';

import { LeagueAvatar } from '@/components/leagues/LeagueAvatar';
import type {
  BulkTradeCounterparty,
  BulkTradeLeagueAvailability,
  TradeDraftPickAsset,
} from '@/types';


export interface BulkTradeCounterpartySelection {
  selected: boolean;
  sendPickOgRosterIdsByRequestIndex: Record<number, number | null>;
  receivePickOgRosterIdsByRequestIndex: Record<number, number | null>;
}


export interface BulkTradeLeagueSelection {
  selected: boolean;
  counterparties: Record<
    number,
    BulkTradeCounterpartySelection
  >;
}


function createCounterpartySelection(
  counterparty: BulkTradeCounterparty,
): BulkTradeCounterpartySelection {
  return {
    selected: true,
    sendPickOgRosterIdsByRequestIndex: Object.fromEntries(
      counterparty.send_pick_choices.map(
        pickChoice => [
          pickChoice.request_index,
          pickChoice.matching_picks[0]?.og_roster_id ?? null,
        ],
      ),
    ),
    receivePickOgRosterIdsByRequestIndex: Object.fromEntries(
      counterparty.receive_pick_choices.map(
        pickChoice => [
          pickChoice.request_index,
          pickChoice.matching_picks[0]?.og_roster_id ?? null,
        ],
      ),
    ),
  };
}


export function createLeagueSelection(
  league: BulkTradeLeagueAvailability,
): BulkTradeLeagueSelection {
  const counterparties = Object.fromEntries(
    league.counterparty_options.map(
      counterparty => [
        counterparty.roster_id,
        createCounterpartySelection(
          counterparty,
        ),
      ],
    ),
  );

  return {
    selected:
      league.counterparty_options.length > 0,
    counterparties,
  };
}


function renderPickSelectionLabel(
  picks: TradeDraftPickAsset[],
  selectedOgRosterId: number | null,
): string {
  const selectedPick = picks.find(
    pick => pick.og_roster_id === selectedOgRosterId,
  );

  return selectedPick?.label ?? 'Choose pick';
}


interface BulkTradeLeagueRowProps {
  league: BulkTradeLeagueAvailability;
  selection: BulkTradeLeagueSelection;
  onChange: (
    nextSelection: BulkTradeLeagueSelection,
  ) => void;
}


export const BulkTradeLeagueRow = ({
  league,
  selection,
  onChange,
}: BulkTradeLeagueRowProps) => {
  if (!league.is_eligible) {
    return (
      <article className="bulk-trade-league-row unavailable">
        <div className="bulk-trade-league-primary">
          <div className="bulk-trade-league-identity">
            <LeagueAvatar
              avatarId={league.league_avatar}
              name={league.league_name}
              size="sm"
            />

            <div>
              <strong>
                {league.league_name}
              </strong>

              <span>
                {league.ineligibility_reason}
              </span>
            </div>
          </div>
        </div>

        <span className="bulk-trade-unavailable">
          Unavailable
        </span>
      </article>
    );
  }

  const counterpartyIds = league.counterparty_options.map(
    counterparty => counterparty.roster_id,
  );

  const selectedCount = counterpartyIds.filter(
    rosterId => selection.counterparties[rosterId]?.selected,
  ).length;

  const allSelected =
    counterpartyIds.length > 0
    && counterpartyIds.every(
      rosterId => selection.counterparties[rosterId]?.selected,
    );

  const toggleLeague = (checked: boolean) => {
    onChange({
      ...selection,
      selected: checked,
      counterparties: Object.fromEntries(
        counterpartyIds.map(rosterId => [
          rosterId,
          {
            ...selection.counterparties[rosterId],
            selected: checked,
          },
        ]),
      ),
    });
  };

  const selectAll = () => {
    onChange({
      ...selection,
      selected: true,
      counterparties: Object.fromEntries(
        counterpartyIds.map(rosterId => [
          rosterId,
          {
            ...selection.counterparties[rosterId],
            selected: true,
          },
        ]),
      ),
    });
  };

  const selectNone = () => {
    onChange({
      ...selection,
      selected: false,
      counterparties: Object.fromEntries(
        counterpartyIds.map(rosterId => [
          rosterId,
          {
            ...selection.counterparties[rosterId],
            selected: false,
          },
        ]),
      ),
    });
  };

  return (
    <article
      className={
        `bulk-trade-league-block ${
          selection.selected
            ? 'selected'
            : ''
        }`
      }
    >
      <div className="bulk-trade-league-block-header">
        <label className="bulk-trade-league-check">
          <input
            type="checkbox"
            checked={selection.selected}
            onChange={event => {
              toggleLeague(event.target.checked);
            }}
          />

          <span />

          <LeagueAvatar
            avatarId={league.league_avatar}
            name={league.league_name}
            size="sm"
          />

          <div className="bulk-trade-league-copy">
            <strong>
              {league.league_name}
            </strong>

            <span>
              {selectedCount >= 2
                ? `Sending to ${selectedCount} managers`
                : selectedCount === 1
                  ? 'Sending to 1 manager'
                  : 'No managers selected'}
            </span>
          </div>
        </label>

        <div className="bulk-trade-league-actions">
          <button
            className="bulk-trade-select-all"
            type="button"
            disabled={allSelected}
            onClick={selectAll}
          >
            <CheckSquare size={14} />
            Select all
          </button>

          <button
            className="bulk-trade-select-none"
            type="button"
            disabled={selectedCount === 0}
            onClick={selectNone}
          >
            <Square size={14} />
            Select none
          </button>
        </div>
      </div>

      <div className="bulk-trade-counterparty-list">
        {
          league.counterparty_options.map(
            counterparty => {
              const counterSelection =
                selection.counterparties[counterparty.roster_id]
                ?? createCounterpartySelection(
                  counterparty,
                );

              const setCounterparty = (
                patch: Partial<BulkTradeCounterpartySelection>,
              ) => {
                onChange({
                  ...selection,
                  selected: true,
                  counterparties: {
                    ...selection.counterparties,
                    [counterparty.roster_id]: {
                      ...counterSelection,
                      ...patch,
                    },
                  },
                });
              };

              return (
                <div
                  key={counterparty.roster_id}
                  className={
                    `bulk-trade-counterparty ${
                      counterSelection.selected
                        ? 'selected'
                        : ''
                    }`
                  }
                >
                  <label className="bulk-trade-counterparty-check">
                    <input
                      type="checkbox"
                      checked={counterSelection.selected}
                      onChange={event => {
                        setCounterparty({
                          selected: event.target.checked,
                        });
                      }}
                    />

                    <span />

                    <strong>
                      {counterparty.name}
                    </strong>
                  </label>

                  <div className="bulk-trade-row-select-group">
                    {
                      counterparty.send_pick_choices.map(
                        pickChoice => (
                          <label
                            key={`${counterparty.roster_id}-send-${pickChoice.request_index}`}
                            className="bulk-trade-row-select"
                          >
                            <span>
                              You send {pickChoice.season} R{pickChoice.round}
                            </span>

                            <select
                              value={
                                counterSelection.sendPickOgRosterIdsByRequestIndex[
                                  pickChoice.request_index
                                ] ?? ''
                              }
                              disabled={
                                !counterSelection.selected
                                || pickChoice.matching_picks.length === 0
                              }
                              onChange={event => {
                                setCounterparty({
                                  sendPickOgRosterIdsByRequestIndex: {
                                    ...counterSelection.sendPickOgRosterIdsByRequestIndex,
                                    [pickChoice.request_index]: (
                                      event.target.value
                                        ? Number(event.target.value)
                                        : null
                                    ),
                                  },
                                });
                              }}
                            >
                              {
                                pickChoice.matching_picks.map(
                                  pick => (
                                    <option
                                      key={`${pickChoice.request_index}-${pick.og_roster_id}`}
                                      value={pick.og_roster_id}
                                    >
                                      {renderPickSelectionLabel(
                                        pickChoice.matching_picks,
                                        pick.og_roster_id,
                                      )}
                                    </option>
                                  ),
                                )
                              }
                            </select>
                          </label>
                        ),
                      )
                    }

                    {
                      counterparty.receive_pick_choices.map(
                        pickChoice => (
                          <label
                            key={`${counterparty.roster_id}-receive-${pickChoice.request_index}`}
                            className="bulk-trade-row-select"
                          >
                            <span>
                              You receive {pickChoice.season} R{pickChoice.round}
                            </span>

                            <select
                              value={
                                counterSelection.receivePickOgRosterIdsByRequestIndex[
                                  pickChoice.request_index
                                ] ?? ''
                              }
                              disabled={
                                !counterSelection.selected
                                || pickChoice.matching_picks.length === 0
                              }
                              onChange={event => {
                                setCounterparty({
                                  receivePickOgRosterIdsByRequestIndex: {
                                    ...counterSelection.receivePickOgRosterIdsByRequestIndex,
                                    [pickChoice.request_index]: (
                                      event.target.value
                                        ? Number(event.target.value)
                                        : null
                                    ),
                                  },
                                });
                              }}
                            >
                              {
                                pickChoice.matching_picks.map(
                                  pick => (
                                    <option
                                      key={`${pickChoice.request_index}-${pick.og_roster_id}`}
                                      value={pick.og_roster_id}
                                    >
                                      {renderPickSelectionLabel(
                                        pickChoice.matching_picks,
                                        pick.og_roster_id,
                                      )}
                                    </option>
                                  ),
                                )
                              }
                            </select>
                          </label>
                        ),
                      )
                    }
                  </div>
                </div>
              );
            },
          )
        }
      </div>
    </article>
  );
};
