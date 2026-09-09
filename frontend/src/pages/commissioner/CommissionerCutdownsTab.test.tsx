import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { CommissionerCutdownsTab } from './CommissionerCutdownsTab';

vi.mock('@/hooks/sleeper/useUsers', () => ({
  useCommissionerCutdowns: () => ({
    data: [
      {
        league_id: '123',
        league_name: 'Test League',
        max_roster_size: 25,
        violations: [
          {
            roster_id: 1,
            owner_id: 'owner-1',
            owner_name: 'Test Manager',
            current_roster_size: 27,
            over_limit_count: 2,
            players_to_cut: [
              {
                player_id: 'p-1',
                full_name: 'Player One',
                position: 'RB',
                team: 'KC',
                ktc_value: 100,
              },
            ],
          },
        ],
      },
    ],
    loading: false,
    fetching: false,
    error: null,
    refetch: vi.fn(),
  }),
  useExecuteCommissionerCutdownAction: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
}));

describe('CommissionerCutdownsTab', () => {
  it('renders Refresh Status button on the same line as the execute action box inside cutdowns-controls-row', () => {
    const { container } = render(<CommissionerCutdownsTab />);

    const controlsRow = container.querySelector('.cutdowns-controls-row');
    expect(controlsRow).toBeInTheDocument();

    const refreshBtn = screen.getByRole('button', { name: /Refresh Status/i });
    expect(controlsRow).toContainElement(refreshBtn);

    const executeBtn = screen.getByRole('button', { name: /Execute Action/i });
    expect(controlsRow).toContainElement(executeBtn);
  });
});
