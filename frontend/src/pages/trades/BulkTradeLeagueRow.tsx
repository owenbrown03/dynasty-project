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
  pickOgRosterId: number | null;
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
      ? league.matching_picks
      : selectedCounterparty?.matching_picks ?? []
  );

  const selectedPick = getPickByOriginalRosterId(
    availablePicks,
    selection.pickOgRosterId,
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
                  const rosterId = Number(
                    event.target.value,
                  );

                  const nextCounterparty = (
                    getCounterpartyByRosterId(
                      league.counterparty_options,
                      rosterId,
                    )
                  );

                  onChange({
                    ...selection,
                    counterpartyRosterId: rosterId,
                    pickOgRosterId: (
                      nextCounterparty?.matching_picks[0]
                        ?.og_roster_id
                      ?? null
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

      <label className="bulk-trade-row-select">
        <span>
          {
            direction === 'buy'
              ? 'You send'
              : 'You receive'
          }
        </span>

        <select
          value={selection.pickOgRosterId ?? ''}
          disabled={
            !selection.selected
            || availablePicks.length === 0
          }
          onChange={event => {
            onChange({
              ...selection,
              pickOgRosterId: Number(
                event.target.value,
              ),
            });
          }}
        >
          {
            availablePicks.map(pick => (
              <option
                key={pick.og_roster_id}
                value={pick.og_roster_id}
              >
                {pick.label}
              </option>
            ))
          }
        </select>
      </label>

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
                Pick: {
                  selectedPick?.label
                  ?? 'No pick selected'
                }
              </span>
            </div>
          )
          : null
      }
    </article>
  );
};