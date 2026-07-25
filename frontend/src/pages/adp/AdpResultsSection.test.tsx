import {
  fireEvent,
  render,
  screen,
} from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { ADPPlayerRow } from '@/types';

import { AdpResultsSection } from './AdpResultsSection';
import {
  buildBoardDisplayRows,
  buildBoardRounds,
} from './adp.utils';

function player(
  id: string,
  name: string,
  position: string,
  overallAdp: number,
): ADPPlayerRow {
  return {
    player_id: id,
    name,
    position,
    team: 'FA',
    overall_adp: overallAdp,
    median_pick: overallAdp,
    min_pick: Math.floor(overallAdp),
    max_pick: Math.ceil(overallAdp),
    standard_deviation: null,
    pick_count: 10,
    draft_count: 10,
    selection_rate: 1,
  };
}

const players = [
  player('1', 'Josh Allen', 'QB', 1.1),
  player('2', 'Bijan Robinson', 'RB', 2.2),
];

describe('AdpResultsSection', () => {
  it('renders board controls and delegates actions', () => {
    const onExportCsv = vi.fn();
    const onViewModeChange = vi.fn();

    render(
      <AdpResultsSection
        dataSource="aggregate"
        generatedAt="2026-07-20T00:00:00Z"
        playerSearch=""
        positionFilter=""
        positionOptions={['QB', 'RB']}
        viewMode="board"
        draftOrderMode="snake"
        sortColumn="overall_adp"
        sortDirection="asc"
        boardPlayers={players}
        sortedPlayers={players}
        totalPlayerCount={2}
        boardSize={2}
        boardDisplayRows={buildBoardDisplayRows(
          buildBoardRounds(players, 2),
          2,
          'snake',
        )}
        onExportCsv={onExportCsv}
        onPlayerSearchChange={vi.fn()}
        onPositionFilterChange={vi.fn()}
        onViewModeChange={onViewModeChange}
        onDraftOrderModeChange={vi.fn()}
        onSortColumnChange={vi.fn()}
        onSortDirectionChange={vi.fn()}
      />,
    );

    expect(screen.getByText('Startup draft board')).toBeInTheDocument();
    expect(screen.getByText('Live aggregate')).toBeInTheDocument();
    expect(screen.getByText('Josh Allen')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Export CSV' }));
    fireEvent.change(screen.getByLabelText('Layout'), {
      target: { value: 'table' },
    });

    expect(onExportCsv).toHaveBeenCalledTimes(1);
    expect(onViewModeChange).toHaveBeenCalledWith('table');
  });

  it('renders the empty state when no rows match', () => {
    render(
      <AdpResultsSection
        dataSource={null}
        generatedAt={null}
        playerSearch=""
        positionFilter=""
        positionOptions={[]}
        viewMode="table"
        draftOrderMode="snake"
        sortColumn="overall_adp"
        sortDirection="asc"
        boardPlayers={[]}
        sortedPlayers={[]}
        totalPlayerCount={0}
        boardSize={12}
        boardDisplayRows={[]}
        onExportCsv={vi.fn()}
        onPlayerSearchChange={vi.fn()}
        onPositionFilterChange={vi.fn()}
        onViewModeChange={vi.fn()}
        onDraftOrderModeChange={vi.fn()}
        onSortColumnChange={vi.fn()}
        onSortDirectionChange={vi.fn()}
      />,
    );

    expect(
      screen.getByText('No qualified players matched this filter set.'),
    ).toBeInTheDocument();
  });
});
