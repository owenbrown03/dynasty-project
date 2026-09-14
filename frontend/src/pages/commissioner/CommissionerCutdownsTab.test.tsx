import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { CommissionerCutdownsTab } from './CommissionerCutdownsTab';

afterEach(() => {
  cleanup();
});

let mockLoading = false;

vi.mock('@/hooks/sleeper/useUsers', () => ({
  useCommissionerCutdowns: () => ({
    data: mockLoading
      ? null
      : [
          {
            league_id: '123',
            league_name: 'Test League',
            max_roster_size: 25,
            violations: [
              {
                roster_id: 1,
                owner_id: 'owner-1',
                owner_name: 'Test Manager',
                roster_size: 27,
                max_roster_size: 25,
                over_limit_count: 2,
                proposed_drops: [
                  {
                    player_id: 'p-1',
                    name: 'Player One',
                    position: 'RB',
                    team: 'KC',
                    ktc_value: 100,
                  },
                ],
              },
            ],
          },
        ],
    loading: mockLoading,
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

  it('switches to Review & Drop and opens preview modal for force drop action', () => {
    render(<CommissionerCutdownsTab />);

    const actionSelect = screen.getByRole('combobox');
    fireEvent.change(actionSelect, { target: { value: 'force_drop' } });

    const reviewBtn = screen.getByRole('button', { name: /Review & Drop/i });
    expect(reviewBtn).toBeInTheDocument();

    // Select the violation checkbox
    const checkbox = screen.getByRole('checkbox');
    fireEvent.click(checkbox);

    // Click Review & Drop
    fireEvent.click(reviewBtn);

    // Modal opens
    expect(screen.getByText('Review Forced Drops')).toBeInTheDocument();
    expect(screen.getByText('Player One')).toBeInTheDocument();
  });

  it('preloads controls and renders detailed skeletons while loading', () => {
    mockLoading = true;
    const { container } = render(<CommissionerCutdownsTab />);

    // Controls are preloaded and visible
    expect(container.querySelector('.cutdowns-controls')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Loading.../i })).toBeInTheDocument();

    // Skeletons are rendered in the grid
    expect(container.querySelectorAll('.commissioner-card').length).toBe(2);
    mockLoading = false;
  });
});
