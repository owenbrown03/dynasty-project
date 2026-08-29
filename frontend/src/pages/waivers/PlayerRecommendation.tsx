import {
  ArrowDownToLine,
  ArrowUpFromLine,
} from 'lucide-react';

import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import { TeamBadge } from '@/components/players/TeamBadge';
import { Skeleton } from '@/components/feedback/Skeleton';
import type {
  PlayerValue,
  ValueBasis,
} from '@/types';

import {
  formatAge,
  formatSelectedValue,
} from './waiver.formatters';


interface PlayerRecommendationProps {
  title: string;
  player: PlayerValue | null | undefined;
  selectedValue?: number | null;
  valueBasis: ValueBasis;
  variant?: 'add' | 'drop';
  type?: 'add' | 'drop';
  loading?: boolean;
  emptyMessage?: string;
  isCheap?: boolean;
}

export const PlayerRecommendation = ({
  title,
  player,
  selectedValue,
  valueBasis,
  variant,
  type,
  loading = false,
  emptyMessage,
  isCheap = false,
}: PlayerRecommendationProps) => {
  const effectiveType = type ?? variant ?? 'add';
  const isAdd = effectiveType === 'add';
  const Icon = isAdd
    ? ArrowUpFromLine
    : ArrowDownToLine;

  return (
    <div className={`waiver-player-card ${isAdd ? 'waiver-player-card-add' : 'waiver-player-card-drop'}`}>
      <div className="waiver-player-card-header">
        <div className="waiver-player-title">
          <Icon size={16} />
          <span>{title}</span>
        </div>

        {isCheap ? (
          <Skeleton variant="text" width="30px" height="14px" />
        ) : player ? (
          <span className="waiver-player-value">
            {formatSelectedValue(
              selectedValue,
              valueBasis,
            )}
          </span>
        ) : null}
      </div>

      {isCheap || loading ? (
        <div className="waiver-player-identity">
          <Skeleton variant="circle" width="32px" height="32px" />
          <div className="waiver-player-copy" style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', flex: 1 }}>
            <Skeleton variant="text" width="60%" height="14px" />
            <Skeleton variant="text" width="40%" height="11px" />
          </div>
        </div>
      ) : player ? (
        <div className="waiver-player-identity">
          <PlayerAvatar
            playerId={player.player_id}
            name={player.name}
            size="sm"
          />

          <div className="waiver-player-copy">
            <div className="waiver-player-name">
              {player.name}
            </div>

            <div className="waiver-player-meta">
              <span>{player.position ?? '—'}</span>
              <span>•</span>
              <TeamBadge team={player.team} size="xs" />
              <span>•</span>
              <span>Age {formatAge(player.age)}</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="waiver-player-empty">
          {emptyMessage ?? 'No player found for this value basis.'}
        </div>
      )}
    </div>
  );
};
