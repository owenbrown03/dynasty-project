import type { CSSProperties } from 'react';

import { PlayerAvatar } from '@/components/players/PlayerAvatar';

import {
  DRAFT_ORDER_LABELS,
  POSITION_THEME_CLASS,
  type BoardDisplayRows,
  type DraftOrderMode,
} from './adp.utils';

interface AdpBoardProps {
  boardDisplayRows: BoardDisplayRows;
  boardSize: number;
  draftOrderMode: DraftOrderMode;
}

export function AdpBoard({
  boardDisplayRows,
  boardSize,
  draftOrderMode,
}: AdpBoardProps) {
  return (
    <>
      <div className="adp-board-note">
        <span className="adp-section-kicker">Board style</span>
        <p>
          Draft-board layout always follows ADP order, grouped into
          {' '}
          {boardSize}
          {' '}
          picks per round. Scroll horizontally to read the full room.
          {' '}
          Visual draft order is set to
          {' '}
          {DRAFT_ORDER_LABELS[draftOrderMode]}.
        </p>
      </div>

      <div className="adp-board">
        <div
          className="adp-board-table-wrap"
          style={
            {
              '--adp-board-columns': String(boardSize),
            } as CSSProperties
          }
        >
          <table className="adp-board-table">
            <thead>
              <tr>
                {Array.from({ length: boardSize }, (_, index) => (
                  <th key={`team-${index + 1}`} className="adp-board-team-header">
                    Team
                    {' '}
                    {index + 1}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {boardDisplayRows.map((roundRow) => (
                <tr key={`round-${roundRow.round}`} className="adp-board-table-row">
                  {roundRow.cells.map((cell) => {
                    const player = cell.entry?.player;
                    const themeClass = POSITION_THEME_CLASS[player?.position ?? ''] ?? '';

                    if (!cell.entry || !player) {
                      return (
                        <td
                          key={`${roundRow.round}-empty-${cell.columnIndex}`}
                          className="adp-board-player-cell"
                        >
                          <article className="adp-player-card adp-player-card-empty">
                            <div className="adp-player-card-topline">
                              <span className="adp-player-slot">
                                {roundRow.round}
                                .
                                {String(cell.displaySlot).padStart(2, '0')}
                              </span>
                            </div>
                          </article>
                        </td>
                      );
                    }

                    return (
                      <td
                        key={`${roundRow.round}-${player.player_id}-${cell.overallPick}`}
                        className="adp-board-player-cell"
                      >
                        <article className={`adp-player-card ${themeClass}`}>
                          <div className="adp-player-card-topline">
                            <span className="adp-player-slot">
                              {roundRow.round}
                              .
                              {String(cell.displaySlot).padStart(2, '0')}
                            </span>
                            <span className="adp-player-rank">{cell.entry.positionRankLabel}</span>
                            <span className="adp-player-average">{player.overall_adp.toFixed(1)}</span>
                          </div>

                          <div className="adp-player-main">
                            <div className="adp-player-copy">
                              <strong className="adp-player-name">{player.name}</strong>
                              <span className="adp-player-meta-compact">
                                {player.position ?? '—'}
                                {' '}
                                ·
                                {' '}
                                {player.team ?? '—'}
                              </span>
                            </div>

                            <PlayerAvatar
                              playerId={player.player_id}
                              name={player.name}
                              size="md"
                              className="adp-player-avatar"
                            />
                          </div>
                        </article>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
