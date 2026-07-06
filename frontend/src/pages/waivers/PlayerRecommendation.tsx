import {
  ArrowDownToLine,
  ArrowUpFromLine,
} from 'lucide-react';

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
}


export const PlayerRecommendation = ({
  title,
  player,
  selectedValue,
  valueBasis,
  variant,
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
          {
            formatSelectedValue(
              selectedValue,
              valueBasis,
            )
          }
        </span>
      </div>

      {
        player
          ? (
            <>
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

              <div className="waiver-player-secondary-values">
                <span>
                  KTC {
                    player.ktc_value !== null
                      ? player.ktc_value.toLocaleString()
                      : '—'
                  }
                </span>

                <span>
                  FC {
                    player.fc_value !== null
                      ? player.fc_value.toLocaleString()
                      : '—'
                  }
                </span>
              </div>
            </>
          )
          : (
            <div className="waiver-player-empty">
              No player found for this value basis.
            </div>
          )
      }
    </div>
  );
};