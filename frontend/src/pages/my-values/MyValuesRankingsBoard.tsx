import { useEffect, useRef, useState } from 'react';

import type { PersonalValueRankingEntry } from '@/types';
import { moveRanking } from './myValues.utils';
import {
  usePersonalValueRankings,
  useResetPersonalValueRankings,
  useSavePersonalValueRankings,
} from '@/hooks/sleeper/usePersonalValues';
import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import { notify } from '@/utils/notify';

import './MyValuesRankingsBoard.css';

const POSITION_OPTIONS = ['QB', 'RB', 'WR', 'TE'];
const VISIBLE_WINDOW = 60;

interface Props {
  leagueId?: string;
  onEditPlayer?: (playerId: string) => void;
}

export function MyValuesRankingsBoard({
  leagueId,
  onEditPlayer,
}: Props) {
  const [position, setPosition] = useState('RB');
  const [scope, setScope] = useState<'current' | 'future'>('future');
  const query = usePersonalValueRankings(
    leagueId,
    position,
    scope,
  );
  const save = useSavePersonalValueRankings();
  const reset = useResetPersonalValueRankings();

  const [override, setOverride] = useState<
    PersonalValueRankingEntry[] | null
  >(null);
  const dragIdRef = useRef<string | null>(null);
  const [dragOverId, setDragOverId] = useState<
    string | null
  >(null);
  const dirtyRef = useRef(false);

  useEffect(() => {
    setOverride(null);
    dirtyRef.current = false;
  }, [
    query.rankings,
    position,
    scope,
  ]);

  const ranked = (
    override ?? query.rankings.filter(
      (entry) => entry.primary_rank !== null,
    )
  ).slice(0, VISIBLE_WINDOW);

  const unrankedCount = query.rankings.length - query.rankings.filter(
    (entry) => entry.primary_rank !== null,
  ).length;

  const handleDragStart = (playerId: string) => {
    dragIdRef.current = playerId;
  };

  // Identity-based swap: hovering another ROW exchanges positions in
  // the current order. Tracking indices instead would oscillate,
  // because the list reflows under the cursor mid-drag.
  const handleDragEnter = (hoverId: string) => {
    const dragId = dragIdRef.current;

    if (!dragId || dragId === hoverId) return;

    setDragOverId(hoverId);

    setOverride((current) => {
      const base = (
        current ?? query.rankings.filter(
          (entry) => entry.primary_rank !== null,
        )
      ).slice(0, VISIBLE_WINDOW);
      const from = base.findIndex(
        (entry) => entry.player_id === dragId,
      );
      const to = base.findIndex(
        (entry) => entry.player_id === hoverId,
      );

      if (from < 0 || to < 0 || from === to) {
        return base;
      }

      dirtyRef.current = true;

      return moveRanking(
        base,
        from,
        to,
      ) as PersonalValueRankingEntry[];
    });
  };

  const commitDrop = async () => {
    dragIdRef.current = null;
    setDragOverId(null);

    const finalOrder = override;

    if (!finalOrder || !dirtyRef.current || !leagueId) {
      return;
    }

    dirtyRef.current = false;

    try {
      await save.saveRankings({
        league_id: leagueId,
        position,
        scope,
        entries: finalOrder.map((entry) => ({
          player_id: entry.player_id,
          primary_rank: entry.primary_rank as number,
        })),
      });
      notify.success(
        scope === 'future'
          ? 'Future-year rankings saved.'
          : 'Current-year rankings saved.',
      );
      setOverride(null);
      dirtyRef.current = false;
    } catch {
      notify.error('Could not save rankings.');
    }
  };

  const handleResetPlayer = async (
    playerId: string,
    name: string,
  ) => {
    if (!leagueId) return;
    if (!window.confirm(`Reset ${name} to Underdog defaults?`)) {
      return;
    }

    try {
      await reset.resetRankings({
        league_id: leagueId,
        position,
        player_id: playerId,
      });
      notify.success(`${name} reset to Underdog defaults.`);
    } catch {
      notify.error('Could not reset player.');
    }
  };

  return (
    <section className="my-values-rankings-board">
      <div className="my-values-rankings-controls">
        <div className="my-values-rankings-positions">
          {POSITION_OPTIONS.map((option) => (
            <button
              key={option}
              type="button"
              className={`my-values-position-chip${position === option ? ' active' : ''}`}
              onClick={() => setPosition(option)}
            >
              {option}
            </button>
          ))}
        </div>

        <div className="my-values-rankings-scope">
          <button
            type="button"
            className={`my-values-scope-chip${scope === 'current' ? ' active' : ''}`}
            onClick={() => setScope('current')}
          >
            Current year ({query.season ?? ''})
          </button>
          <button
            type="button"
            className={`my-values-scope-chip${scope === 'future' ? ' active' : ''}`}
            onClick={() => setScope('future')}
          >
            Future years
          </button>
        </div>

      </div>

      <p className="my-values-rankings-hint">
        Drag to reorder — saves automatically.
        {' '}<span className="my-values-rank-asterisk">*</span> marks players
        with individually edited future years; board moves never touch those.
      </p>

      {query.loading ? (
        <p className="page-description">Loading rankings…</p>
      ) : (
        <>
          <ol className="my-values-ranking-list">
            {ranked.map((entry) => (
              <li
                key={entry.player_id}
                className={`my-values-ranking-row${dragOverId === entry.player_id && dragIdRef.current !== null ? ' drag-target' : ''}`}
                draggable
                onDragStart={(event) => {
                  event.dataTransfer.effectAllowed = 'move';
                  handleDragStart(entry.player_id);
                }}
                onDragEnter={() => handleDragEnter(entry.player_id)}
                onDragOver={(event) => event.preventDefault()}
                onDrop={(event) => event.preventDefault()}
                onDragEnd={() => {
                  void commitDrop();
                }}
              >
                <span className="my-values-rank-number">
                  {entry.primary_rank}
                </span>
                <span className="my-values-rank-name">
                  <PlayerAvatar
                    playerId={entry.player_id}
                    name={entry.name}
                    size="sm"
                  />
                  <span className="my-values-rank-name-text">
                    {entry.name}
                    {scope === 'future'
                      && entry.has_divergent_future_years ? (
                        <span className="my-values-rank-asterisk">*</span>
                      ) : null}
                  </span>
                </span>
                <span className="my-values-rank-meta">
                  {[
                    entry.position,
                    entry.team,
                    ...entry.outcomes.map(
                      (outcome) =>
                        `${outcome.position_rank} @ ${Math.round(outcome.probability)}%`,
                    ),
                  ]
                    .filter(Boolean)
                    .join(' · ')}
                </span>
                <button
                  type="button"
                  className="my-values-rank-reset"
                  title="Edit outcomes in editor"
                  onClick={() => onEditPlayer?.(entry.player_id)}
                >
                  ✎
                </button>
                <button
                  type="button"
                  className="my-values-rank-reset"
                  title="Reset to Underdog defaults"
                  disabled={reset.saving}
                  onClick={() => {
                    void handleResetPlayer(
                      entry.player_id,
                      entry.name,
                    );
                  }}
                >
                  ↺
                </button>
              </li>
            ))}
          </ol>

          {unrankedCount > 0 && (
            <p className="page-description">
              +{unrankedCount} unranked players not shown.
            </p>
          )}
        </>
      )}
    </section>
  );
}


