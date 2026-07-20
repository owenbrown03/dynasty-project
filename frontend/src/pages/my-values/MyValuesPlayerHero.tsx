import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import type { PersonalValuePlayer } from '@/types';
import { getPositionColor } from '@/utils/positions';
import { formatMarketNumber } from './myValues.utils';

interface MyValuesPlayerHeroProps {
  player: PersonalValuePlayer;
  playerInPool: boolean;
  saving: boolean;
  onReset: () => void;
  onSave: () => void;
}

export function MyValuesPlayerHero({
  player,
  playerInPool,
  saving,
  onReset,
  onSave,
}: MyValuesPlayerHeroProps) {
  return (
    <div className="my-values-player-hero">
      <div className="my-values-player-identity">
        <PlayerAvatar
          playerId={player.player_id}
          name={player.name}
          size="lg"
        />
        <div>
          <div className="my-values-player-tag-row">
            <span
              className="my-values-player-position"
              style={{
                color: getPositionColor(
                  player.position,
                ),
              }}
            >
              {player.position}
            </span>
            <span>{player.team ?? '--'}</span>
            <span>Age {player.age ?? '--'}</span>
            <span>{player.underdog_position_rank ?? 'No UD rank'}</span>
            <span>KTC {formatMarketNumber(player.ktc_value)}</span>
            <span>FC {formatMarketNumber(player.fc_value)}</span>
            <span>ADP {formatMarketNumber(player.adp_value)}</span>
          </div>
          <h2>{player.name}</h2>
          <p>
            {playerInPool
              ? 'Editing a player already in your active projection pool.'
              : 'This player will join your saved projection pool once you save a custom projection.'}
          </p>
        </div>
      </div>

      <div className="my-values-player-actions">
        <button
          type="button"
          className="button-secondary"
          onClick={onReset}
          disabled={saving}
        >
          Reset view
        </button>
        <button
          type="button"
          className="button-secondary"
          onClick={onSave}
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Save projections'}
        </button>
      </div>
    </div>
  );
}
