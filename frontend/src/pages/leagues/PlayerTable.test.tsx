import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { PlayerTable } from './PlayerTable';
import type { LeaguePlayer } from '@/types';

const mockPlayers: LeaguePlayer[] = [
  {
    player_id: '1',
    name: 'Josh Allen',
    position: 'QB',
    team: 'BUF',
    is_starter: true,
    starter_slot: 'QB',
    fantasycalc_value: 8000,
    ktc_value: 8500,
    projected_points: 22.5,
    underdog_position_rank: 1,
    redraft_starter_war: 2.5,
    redraft_roster_war: 3.0,
    dynasty_starter_war: 4.0,
    dynasty_roster_war: 4.5,
    my_redraft_starter_war: 2.8,
    my_redraft_roster_war: 3.2,
    my_dynasty_starter_war: 4.2,
    my_dynasty_roster_war: 4.8,
  },
  {
    player_id: '2',
    name: 'Breece Hall',
    position: 'RB',
    team: 'NYJ',
    is_starter: false,
    starter_slot: null,
    fantasycalc_value: 6000,
    ktc_value: 6200,
    projected_points: 15.0,
    underdog_position_rank: 5,
    redraft_starter_war: 1.5,
    redraft_roster_war: 2.0,
    dynasty_starter_war: 3.0,
    dynasty_roster_war: 3.5,
    my_redraft_starter_war: 1.8,
    my_redraft_roster_war: 2.2,
    my_dynasty_starter_war: 3.2,
    my_dynasty_roster_war: 3.8,
  },
];

describe('PlayerTable', () => {
  it('renders table headers and player rows with sticky table structure', () => {
    const { container } = render(
      <PlayerTable
        players={mockPlayers}
        emptyStarterSlots={[]}
        valueBasis="ktc"
        redraftValueBasis="sleeper_projection"
        warValueSettings={{
          sleeper_projection: {
            timeframe: 'dynasty',
            scope: 'roster',
          },
          my: {
            timeframe: 'dynasty',
            scope: 'roster',
          },
        }}
      />,
    );

    const table = container.querySelector('table.player-table');
    expect(table).toBeInTheDocument();

    const thead = table?.querySelector('thead');
    expect(thead).toBeInTheDocument();

    const headers = screen.getAllByRole('columnheader');
    expect(headers.length).toBeGreaterThan(0);
    expect(screen.getByRole('columnheader', { name: 'Slot' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: 'Name' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: 'Pos' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: 'Team' })).toBeInTheDocument();
    expect(screen.getAllByRole('columnheader', { name: 'Proj' }).length).toBeGreaterThan(0);
    expect(screen.getByRole('columnheader', { name: 'UD' })).toBeInTheDocument();

    expect(screen.getByText('Josh Allen')).toBeInTheDocument();
    expect(screen.getByText('Breece Hall')).toBeInTheDocument();
  });
});
