import {
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import {
  useMemo,
  useState,
} from 'react';

import { LeagueAvatar } from '@/components/leagues/LeagueAvatar';
import type {
  BulkTradeCounterparty,
  BulkTradeLeagueAvailability,
  TradeDraftPickAsset,
} from '@/types';


export interface BulkTradeLeagueSelection {
  selected: boolean;
  counterpartyRosterId: number | null;
  sendPickOgRosterIdsByRequestIndex: Record<number, number | null>;
  receivePickOgRosterIdsByRequestIndex: Record<number, number | null>;
}


interface BulkTradeLeagueRowProps {
  league: BulkTradeLeagueAvailability;
  selection: BulkTradeLeagueSelection;
  onChange: (
    nextSelection: BulkTradeLeagueSelection,
  ) => void;
}


function getCounterpartyByRosterId(
  counterparties: BulkTradeCounterparty[],
  rosterId: number | null,
): BulkTradeCounterparty | null {
  if (rosterId === null) {
    return null;
  }

  return counterparties.find(
    counterparty => counterparty.roster_id === rosterId,
  ) ?? null;
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


export const BulkTradeLeagueRow = ({
  league,
  selection,
  onChange,
}: BulkTradeLeagueRowProps) => {
  const [showDetails, setShowDetails] = useState(
    false,
  );

  const selectedCounterparty = useMemo(
    () => getCounterpartyByRosterId(
      league.counterparty_options,
      selection.counterpartyRosterId,
    ),
    [
      league.counterparty_options,
      selection.counterpartyRosterId,
    ],
  );

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

  return (
    <article
      className={
        `bulk-trade-league-row ${
          selection.selected
            ? 'selected'
            : ''
        }`
      }
    >
      <label className="bulk-trade-row-toggle">
        <input
          type="checkbox"
          checked={selection.selected}
          onChange={event => {
            onChange({
              ...selection,
              selected: event.target.checked,
            });
          }}
        />

        <span />
      </label>

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
              Trade with{' '}
              {selectedCounterparty?.name ?? 'Choose manager'}
            </span>
          </div>
        </div>
      </div>

      <label className="bulk-trade-row-select">
        <span>
          Manager
        </span>

        <select
          value={selection.counterpartyRosterId ?? ''}
          disabled={!selection.selected}
          onChange={event => {
            const rosterId = event.target.value
              ? Number(event.target.value)
              : null;

            const nextCounterparty = getCounterpartyByRosterId(
              league.counterparty_options,
              rosterId,
            );

            onChange({
              ...selection,
              counterpartyRosterId: rosterId,
              sendPickOgRosterIdsByRequestIndex: Object.fromEntries(
                (nextCounterparty?.send_pick_choices ?? []).map(
                  pickChoice => [
                    pickChoice.request_index,
                    pickChoice.matching_picks[0]?.og_roster_id ?? null,
                  ],
                ),
              ),
              receivePickOgRosterIdsByRequestIndex: Object.fromEntries(
                (nextCounterparty?.receive_pick_choices ?? []).map(
                  pickChoice => [
                    pickChoice.request_index,
                    pickChoice.matching_picks[0]?.og_roster_id ?? null,
                  ],
                ),
              ),
            });
          }}
        >
          {
            league.counterparty_options.map(
              counterparty => (
                <option
                  key={counterparty.roster_id}
                  value={counterparty.roster_id}
                >
                  {counterparty.name}
                </option>
              ),
            )
          }
        </select>
      </label>

      <div className="bulk-trade-row-select-group">
        {
          (selectedCounterparty?.send_pick_choices ?? []).map(
            pickChoice => (
              <label
                key={`${league.league_id}-send-${pickChoice.request_index}`}
                className="bulk-trade-row-select"
              >
                <span>
                  You send {pickChoice.season} R{pickChoice.round}
                </span>

                <select
                  value={
                    selection.sendPickOgRosterIdsByRequestIndex[
                      pickChoice.request_index
                    ] ?? ''
                  }
                  disabled={
                    !selection.selected
                    || pickChoice.matching_picks.length === 0
                  }
                  onChange={event => {
                    onChange({
                      ...selection,
                      sendPickOgRosterIdsByRequestIndex: {
                        ...selection.sendPickOgRosterIdsByRequestIndex,
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
          (selectedCounterparty?.receive_pick_choices ?? []).map(
            pickChoice => (
              <label
                key={`${league.league_id}-receive-${pickChoice.request_index}`}
                className="bulk-trade-row-select"
              >
                <span>
                  You receive {pickChoice.season} R{pickChoice.round}
                </span>

                <select
                  value={
                    selection.receivePickOgRosterIdsByRequestIndex[
                      pickChoice.request_index
                    ] ?? ''
                  }
                  disabled={
                    !selection.selected
                    || pickChoice.matching_picks.length === 0
                  }
                  onChange={event => {
                    onChange({
                      ...selection,
                      receivePickOgRosterIdsByRequestIndex: {
                        ...selection.receivePickOgRosterIdsByRequestIndex,
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

      <button
        className="bulk-trade-row-details"
        type="button"
        onClick={() => {
          setShowDetails(current => !current);
        }}
      >
        {
          showDetails
            ? <ChevronUp size={16} />
            : <ChevronDown size={16} />
        }
        Details
      </button>

      {
        showDetails
          ? (
            <div className="bulk-trade-row-detail-copy">
              <span>
                Counterparties who can satisfy the full mixed package in this league are listed above.
              </span>
            </div>
          )
          : null
      }
    </article>
  );
};
