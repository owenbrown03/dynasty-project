import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router';

import { PlayerTable } from './PlayerTable';
import type { LeaguePlayer } from '@/types';

afterEach(() => {
  cleanup();
});

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

function renderWithProviders(ui: React.ReactElement) {
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        {ui}
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const mockPlayers: LeaguePlayer[] = [
  {
    player_id: '1',
    name: 'Josh Allen',
    position: 'QB',
    team: 'BUF',
    age: 28,
    is_starter: true,
    slot: 'QB',
    fc_value: 8000,
    ktc_value: 8500,
    fc_trend_30_day: 0,
    projected_points: 22.5,
    underdog_position_rank: '1',
    redraft_starter_war: 2.5,
    redraft_roster_war: 3.0,
    dynasty_starter_war: 4.0,
    dynasty_roster_war: 4.5,
    my_redraft_starter_war: 2.8,
    my_redraft_roster_war: 3.2,
    my_dynasty_starter_war: 4.2,
    my_dynasty_roster_war: 4.8,
    on_block: false,
  },
  {
    player_id: '2',
    name: 'Breece Hall',
    position: 'RB',
    team: 'NYJ',
    age: 23,
    is_starter: false,
    slot: null,
    fc_value: 6000,
    ktc_value: 6200,
    fc_trend_30_day: 0,
    projected_points: 15.0,
    underdog_position_rank: '5',
    redraft_starter_war: 1.5,
    redraft_roster_war: 2.0,
    dynasty_starter_war: 3.0,
    dynasty_roster_war: 3.5,
    my_redraft_starter_war: 1.8,
    my_redraft_roster_war: 2.2,
    my_dynasty_starter_war: 3.2,
    my_dynasty_roster_war: 3.8,
    on_block: true,
  },
];

describe('PlayerTable', () => {
  it('renders table headers, player rows, trade buttons, and trade block actions', () => {
    const { container } = renderWithProviders(
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
        leagueId="12345"
        isUserRoster={true}
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
    expect(screen.getByRole('columnheader', { name: 'Actions' })).toBeInTheDocument();

    expect(screen.getByText('Josh Allen')).toBeInTheDocument();
    expect(screen.getByText('Breece Hall')).toBeInTheDocument();

    // Verify Trade buttons are rendered
    const tradeButtons = screen.getAllByRole('button', { name: /trade/i });
    expect(tradeButtons.length).toBe(2);

    // Verify Trade Block buttons are rendered for user roster
    expect(screen.getByRole('button', { name: /\+ Block/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /On Block/i })).toBeInTheDocument();
  });
});

