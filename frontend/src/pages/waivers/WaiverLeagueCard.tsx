import {
  ArrowRight,
  CircleDollarSign,
  Users,
} from 'lucide-react';

import type { WaiverLeagueOverview } from '@/types';

import { formatSelectedValue } from './waiver.formatters';
import { PlayerRecommendation } from './PlayerRecommendation';
import { WaiverClaimAction } from './WaiverClaimAction';


interface WaiverLeagueCardProps {
  league: WaiverLeagueOverview;
}


export const WaiverLeagueCard = ({
  league,
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
      : undefined
  );

  return (
    <article className="waiver-league-card">
      <div className="waiver-league-header">
        <div>
          <h2>
            {league.league_name}
          </h2>

          <p>
            {league.value_label}
          </p>
        </div>

        <div className="waiver-gain">
          <span>
            Value Gain
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