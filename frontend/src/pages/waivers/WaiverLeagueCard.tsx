import {
  ArrowRight,
  CircleDollarSign,
  DoorOpen,
  Search,
  Users,
} from 'lucide-react';

import { LeagueAvatar } from '@/components/leagues/LeagueAvatar';
import type { WaiverLeagueOverview } from '@/types';

import { formatSelectedValue } from './waiver.formatters';
import { PlayerRecommendation } from './PlayerRecommendation';
import { WaiverClaimAction } from './WaiverClaimAction';


interface WaiverLeagueCardProps {
  league: WaiverLeagueOverview;
  onOpenAvailableLeague: (
    leagueId: string,
  ) => void;
}


export const WaiverLeagueCard = ({
  league,
  onOpenAvailableLeague,
}: WaiverLeagueCardProps) => {
  const rosterStatusClass = (
    league.roster_spots_available < 0
      ? 'negative'
      : league.roster_spots_available === 0
        ? 'neutral'
        : 'positive'
  );

  const claimBlockedReason = (
    league.roster_spots_available < 0
      ? (
        `Roster is ${
          Math.abs(
            league.roster_spots_available,
          )
        } players over capacity. Remove players before claiming.`
      )
      : league.value_gain === null
        ? 'No positive waiver swap available right now.'
      : undefined
  );

  return (
    <article className="waiver-league-card">
      <div className="waiver-league-header">
        <div className="waiver-league-identity">
          <LeagueAvatar
            avatarId={league.league_avatar}
            name={league.league_name}
            size="md"
          />

          <div>
            <button
              type="button"
              className="waiver-league-link-button"
              onClick={() => {
                onOpenAvailableLeague(
                  league.league_id,
                );
              }}
            >
              <h2>
                {league.league_name}
              </h2>
            </button>

            <p className="waiver-league-basis">
              Evaluated by {league.value_label}
            </p>
          </div>
        </div>

        <div className="waiver-gain">
          <span>
            Net gain
          </span>

          <strong>
            +{
              formatSelectedValue(
                league.value_gain,
                league.value_basis,
              )
            }
          </strong>
        </div>
      </div>

      <div className="waiver-league-stats">
        <div className="waiver-stat">
          <Users size={15} />

          <span>
            Roster
          </span>

          <strong>
            {league.roster_size}
            /
            {league.roster_capacity}
          </strong>
        </div>

        <div className="waiver-stat">
          <DoorOpen size={15} />

          <span>
            Open Spots
          </span>

          <strong
            className={
              `waiver-roster-status ${
                rosterStatusClass
              }`
            }
          >
            {league.roster_spots_available}
          </strong>
        </div>

        <div className="waiver-stat">
          <CircleDollarSign size={15} />

          <span>
            FAAB
          </span>

          <strong>
            ${league.faab_remaining}

            <small>
              /${league.faab_budget}
            </small>
          </strong>
        </div>

        <div className="waiver-stat">
          <Search size={15} />

          <span>
            Available
          </span>

          <strong>
            {league.available_player_count.toLocaleString()}
          </strong>
        </div>
      </div>

      <div className="waiver-recommendation-grid">
        <PlayerRecommendation
          title="Suggested Add"
          player={league.suggested_add}
          selectedValue={league.suggested_add_value}
          valueBasis={league.value_basis}
          variant="add"
          emptyMessage="No positive add recommended right now."
        />

        <div className="waiver-swap-arrow">
          <ArrowRight size={22} />
        </div>

        <PlayerRecommendation
          title="Suggested Drop"
          player={league.suggested_drop}
          selectedValue={league.suggested_drop_value}
          valueBasis={league.value_basis}
          variant="drop"
          emptyMessage="No drop needed for a positive swap right now."
        />
      </div>

      <div className="waiver-league-footer">
        <span>
          FAAB remaining: {league.faab_percent_remaining}%
        </span>

        <WaiverClaimAction
          league={league}
          disabled={!!claimBlockedReason}
          disabledReason={claimBlockedReason}
        />
      </div>
    </article>
  );
};
