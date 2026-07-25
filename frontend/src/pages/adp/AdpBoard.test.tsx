import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import type { ADPPlayerRow } from '@/types';

import { AdpBoard } from './AdpBoard';
import {
  buildBoardDisplayRows,
  buildBoardRounds,
} from './adp.utils';

function player(
  id: string,
  name: string,
  position: string,
  team: string,
  overallAdp: number,
): ADPPlayerRow {
  return {
    player_id: id,
    name,
    position,
    team,
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

describe('AdpBoard', () => {
  it('renders board rows with teams, player slots, ranks, and ADP', () => {
    const rounds = buildBoardRounds(
      [
        player('1', 'Josh Allen', 'QB', 'BUF', 1.2),
        player('2', 'Bijan Robinson', 'RB', 'ATL', 2.4),
        player('3', 'JaMarr Chase', 'WR', 'CIN', 3.6),
        player('4', 'Brock Bowers', 'TE', 'LV', 4.8),
      ],
      2,
    );
    const boardDisplayRows = buildBoardDisplayRows(rounds, 2, 'snake');

    const { container } = render(
      <AdpBoard
        boardDisplayRows={boardDisplayRows}
        boardSize={2}
        draftOrderMode="snake"
      />,
    );

    expect(screen.getByText('Team 1')).toBeInTheDocument();
    expect(screen.getByText('Team 2')).toBeInTheDocument();
    expect(screen.getByText('Josh Allen')).toBeInTheDocument();
    expect(screen.getByText('Bijan Robinson')).toBeInTheDocument();
    expect(screen.getByText('QB1')).toBeInTheDocument();
    expect(screen.getByText('RB1')).toBeInTheDocument();
    expect(screen.getByText('1.2')).toBeInTheDocument();
    expect(container.textContent).toContain('1.01');
    expect(container.textContent).toContain('2.02');
  });
});
