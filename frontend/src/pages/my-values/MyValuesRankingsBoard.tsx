import { useEffect, useRef, useState } from 'react';

import type { PersonalValueRankingEntry } from '@/types';
import { moveRanking } from './myValues.utils';
import {
  usePersonalValueRankings,
  useResetPersonalValueRankings,
  useSavePersonalValueRankings,
} from '@/hooks/sleeper/usePersonalValues';
import { notify } from '@/utils/notify';

import './MyValuesRankingsBoard.css';

const POSITION_OPTIONS = ['QB', 'RB', 'WR', 'TE'];
const VISIBLE_WINDOW = 60;

interface Props {
  leagueId?: string;
}

export function MyValuesRankingsBoard({ leagueId }: Props) {
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
  const dragIndex = useRef<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<
    number | null
  >(null);

  useEffect(() => {
    setOverride(null);
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

  const handleDragStart = (index: number) => {
    dragIndex.current = index;
  };

  const handleDragEnter = (index: number) => {
    if (dragIndex.current === null) return;
    setDragOverIndex(index);

    setOverride((current) => {
      const base = current ?? query.rankings.filter(
        (entry) => entry.primary_rank !== null,
      );
      return moveRanking(
        base.slice(0, VISIBLE_WINDOW),
        dragIndex.current as number,
        index,
      ) as PersonalValueRankingEntry[];
    });
    dragIndex.current = index;
  };

  const commitDrop = async () => {
    dragIndex.current = null;
    setDragOverIndex(null);

    if (!override || !leagueId || save.saving) {
      return;
    }

    try {
      await save.saveRankings({
        league_id: leagueId,
        position,
        scope,
        entries: override.map((entry) => ({
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

  const handleResetAll = async () => {
    if (!leagueId) return;
    if (
      !window.confirm(
        `Remove ALL your customizations for ${position}s and reset every ${position} to Underdog defaults?`,
      )
    ) {
      return;
    }

    try {
      const result = await reset.resetRankings({
        league_id: leagueId,
        position,
      });
      notify.success(
        `Reset ${result.reset_players} ${position}s to Underdog defaults.`,
      );
      setOverride(null);
    } catch {
      notify.error('Could not reset rankings.');
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

        <button
          type="button"
          className="button-secondary my-values-reset-all"
          disabled={reset.saving}
          onClick={() => {
            void handleResetAll();
          }}
        >
          Reset all {position}s to Underdog
        </button>
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
            {ranked.map((entry, index) => (
              <li
                key={entry.player_id}
                className={`my-values-ranking-row${dragOverIndex === index && dragIndex.current !== null ? ' drag-target' : ''}`}
                draggable
                onDragStart={() => handleDragStart(index)}
                onDragEnter={() => handleDragEnter(index)}
                onDragOver={(event) => event.preventDefault()}
                onDragEnd={() => {
                  void commitDrop();
                }}
                onDrop={(event) => {
                  event.preventDefault();
                  void commitDrop();
                }}
              >
                <span className="my-values-rank-number">
                  {entry.primary_rank}
                </span>
                <span className="my-values-rank-name">
                  {entry.name}
                  {scope === 'future'
                    && entry.has_divergent_future_years ? (
                      <span className="my-values-rank-asterisk">*</span>
                    ) : null}
                </span>
                <span className="my-values-rank-meta">
                  {[
                    entry.position,
                    entry.team,
                    entry.secondary_rank != null
                      ? `${entry.primary_rank} / ${entry.secondary_rank}`
                      : null,
                  ]
                    .filter(Boolean)
                    .join(' · ')}
                </span>
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


