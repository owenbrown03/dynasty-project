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
  TradeDirection,
  TradeDraftPickAsset,
} from '@/types';


export interface BulkTradeLeagueSelection {
  selected: boolean;
  counterpartyRosterId: number | null;
  pickOgRosterIdsByRequestIndex: Record<number, number | null>;
}


interface BulkTradeLeagueRowProps {
  league: BulkTradeLeagueAvailability;
  direction: TradeDirection;
  selection: BulkTradeLeagueSelection;
  onChange: (
    nextSelection: BulkTradeLeagueSelection,
  ) => void;
}


function getPickByOriginalRosterId(
  picks: TradeDraftPickAsset[],
  ogRosterId: number | null,
): TradeDraftPickAsset | null {
  if (ogRosterId === null) {
    return null;
  }

  return picks.find(
    pick => pick.og_roster_id === ogRosterId,
  ) ?? null;
}


function getCounterpartyByRosterId(
  counterparties: BulkTradeCounterparty[],
  rosterId: number | null,
): BulkTradeCounterparty | null {
  if (rosterId === null) {
    return null;
  }

  return counterparties.find(
    counterparty => (
      counterparty.roster_id === rosterId
    ),
  ) ?? null;
}


export const BulkTradeLeagueRow = ({
  league,
  direction,
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

  const availablePicks = (
    direction === 'buy'
      ? league.pick_choices
      : selectedCounterparty?.pick_choices ?? []
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

  const targetManagerLabel = (
    direction === 'buy'
      ? league.target_owner_name ?? 'Unknown manager'
      : selectedCounterparty?.name ?? 'Choose manager'
  );

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
              {
                direction === 'buy'
                  ? `Buy from ${targetManagerLabel}`
                  : `Sell to ${targetManagerLabel}`
              }
            </span>
          </div>
        </div>
      </div>

      {
        direction === 'sell'
          ? (
            <label className="bulk-trade-row-select">
              <span>
                Manager
              </span>

              <select
                value={
                  selection.counterpartyRosterId
                  ?? ''
                }
                disabled={!selection.selected}
                onChange={event => {
                  const rosterId = event.target.value
                    ? Number(event.target.value)
                    : null;

                  const nextCounterparty = (
                    getCounterpartyByRosterId(
                      league.counterparty_options,
                      rosterId,
                    )
                  );

                  onChange({
                    ...selection,
                    counterpartyRosterId: rosterId,
                    pickOgRosterIdsByRequestIndex: Object.fromEntries(
                      (nextCounterparty?.pick_choices ?? []).map(
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
          )
          : null
      }

      <div className="bulk-trade-row-select-group">
        {
          availablePicks.map(
            pickChoice => (
              <label
                key={`${league.league_id}-${pickChoice.request_index}`}
                className="bulk-trade-row-select"
              >
                <span>
                  {
                    direction === 'buy'
                      ? `You send ${pickChoice.season} R${pickChoice.round}`
                      : `You receive ${pickChoice.season} R${pickChoice.round}`
                  }
                </span>

                <select
                  value={
                    selection.pickOgRosterIdsByRequestIndex[
                      pickChoice.request_index
                    ] ?? ''
                  }
                  disabled={
                    !selection.selected
                    || pickChoice.matching_picks.length === 0
                  }
                  onChange={event => {
                    const nextOriginalRosterId = event.target.value
                      ? Number(event.target.value)
                      : null;

                    onChange({
                      ...selection,
                      pickOgRosterIdsByRequestIndex: {
                        ...selection.pickOgRosterIdsByRequestIndex,
                        [pickChoice.request_index]: nextOriginalRosterId,
                      },
                    });
                  }}
                >
                  {
                    pickChoice.matching_picks.map(pick => (
                      <option
                        key={`${pickChoice.request_index}-${pick.og_roster_id}`}
                        value={pick.og_roster_id}
                      >
                        {pick.label}
                      </option>
                    ))
                  }
                </select>
              </label>
            ),
          )
        }
      </div>

      <button
        className="bulk-trade-details-button"
        onClick={() => {
          setShowDetails(
            current => !current,
          );
        }}
        title="Show trade details"
      >
        {
          showDetails
            ? <ChevronUp size={16} />
            : <ChevronDown size={16} />
        }
      </button>

      {
        showDetails
          ? (
            <div className="bulk-trade-row-details">
              <span>
                Your roster: #{league.your_roster_id}
              </span>

              <span>
                Counterparty roster: {
                  direction === 'buy'
                    ? league.target_owner_roster_id
                    : selection.counterpartyRosterId
                }
              </span>

              <span>
                Picks: {
                  availablePicks.map(pickChoice => {
                    const selectedPick = getPickByOriginalRosterId(
                      pickChoice.matching_picks,
                      selection.pickOgRosterIdsByRequestIndex[
                        pickChoice.request_index
                      ] ?? null,
                    );

                    return selectedPick?.label ?? `${pickChoice.season} Round ${pickChoice.round}`;
                  }).join(', ')
                }
              </span>
            </div>
          )
          : null
      }
    </article>
  );
};
