import {
  ArrowDownToLine,
  ArrowUpFromLine,
} from 'lucide-react';

import { PlayerAvatar } from '@/components/players/PlayerAvatar';
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
  player: PlayerValue | null;
  selectedValue: number | null;
  valueBasis: ValueBasis;
  variant: 'add' | 'drop';
  emptyMessage?: string;
  isCheap?: boolean;
}


export const PlayerRecommendation = ({
  title,
  player,
  selectedValue,
  valueBasis,
  variant,
  emptyMessage,
  isCheap,
}: PlayerRecommendationProps) => {
  const isAdd = variant === 'add';

  return (
    <div
      className={
        `waiver-player-card ${
          isAdd
            ? 'waiver-player-card-add'
            : 'waiver-player-card-drop'
        }`
      }
    >
      <div className="waiver-player-card-header">
        <div className="waiver-player-title">
          {
            isAdd
              ? <ArrowUpFromLine size={16} />
              : <ArrowDownToLine size={16} />
          }

          <span>{title}</span>
        </div>

        <span className="waiver-player-value">
          {isCheap ? (
            <Skeleton variant="text" width="30px" height="14px" />
          ) : (
            formatSelectedValue(
              selectedValue,
              valueBasis,
            )
          )}
        </span>
      </div>

      {isCheap ? (
        <div className="waiver-player-identity">
          <Skeleton variant="circle" width="40px" height="40px" />
          <div className="waiver-player-copy" style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', flex: 1 }}>
            <Skeleton variant="text" width="60%" height="16px" />
            <Skeleton variant="text" width="40%" height="12px" />
          </div>
        </div>
      ) : player ? (
        <>
          <div className="waiver-player-identity">
            <PlayerAvatar
              playerId={player.player_id}
              name={player.name}
              size="md"
            />

            <div className="waiver-player-copy">
              <div className="waiver-player-name">
                {player.name}
              </div>

              <div className="waiver-player-meta">
                <span>
                  {player.position ?? '—'}
                </span>

                <span>•</span>

                <span>
                  {player.team ?? 'FA'}
                </span>

                <span>•</span>

                <span>
                  Age {formatAge(player.age)}
                </span>
              </div>
            </div>
          </div>
        </>
      ) : (
        <div className="waiver-player-empty">
          {emptyMessage ?? 'No player found for this value basis.'}
        </div>
      )}
    </div>
  );
};
