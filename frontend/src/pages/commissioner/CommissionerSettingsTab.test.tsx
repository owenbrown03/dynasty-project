import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { CommissionerSettingsTab } from './CommissionerSettingsTab';

afterEach(() => {
  cleanup();
});

const mockMutateAsync = vi.fn().mockResolvedValue({ successful_leagues: 1, results: [] });

vi.mock('@/utils/notify', () => ({
  notify: {
    success: vi.fn(),
    error: vi.fn(),
    dismiss: vi.fn(),
  },
}));

const mockOverviewData = [
  {
    league_id: 'l1',
    league_name: 'Best Ball League Alpha',
    avatar: null,
    total_rosters: 12,
    best_ball: 1,
    bench_lock: 0,
    disable_adds: 0,
    offseason_adds: 0,
    disable_trades: 0,
    trade_deadline: 11,
    pick_trading: 1,
    trade_review_days: 0,
    veto_auto_poll: 0,
    veto_show_votes: 0,
    veto_votes_needed: 0,
    playoff_teams: 6,
    playoff_week_start: 15,
    league_average_match: 0,
    waiver_bid_min: 0,
    taxi_deadline: 0,
    taxi_allow_vets: 0,
    taxi_years: 0,
    reserve_allow_out: 1,
    reserve_allow_doubtful: 0,
    reserve_allow_sus: 0,
    reserve_allow_cov: 0,
    reserve_allow_na: 0,
    reserve_allow_dnr: 0,
  },
  {
    league_id: 'l2',
    league_name: 'Lineup League Beta',
    avatar: null,
    total_rosters: 10,
    best_ball: 0,
    bench_lock: 1,
    disable_adds: 0,
    offseason_adds: 1,
    disable_trades: 0,
    trade_deadline: 99,
    pick_trading: 1,
    trade_review_days: 2,
    veto_auto_poll: 0,
    veto_show_votes: 0,
    veto_votes_needed: 0,
    playoff_teams: 4,
    playoff_week_start: 15,
    league_average_match: 1,
    waiver_bid_min: 0,
    taxi_deadline: 0,
    taxi_allow_vets: 0,
    taxi_years: 0,
    reserve_allow_out: 1,
    reserve_allow_doubtful: 0,
    reserve_allow_sus: 0,
    reserve_allow_cov: 0,
    reserve_allow_na: 0,
    reserve_allow_dnr: 0,
  },
];

vi.mock('@/hooks/sleeper/useUsers', () => ({
  useCommissionerSettingsOverview: () => ({
    data: mockOverviewData,
    isLoading: false,
    isFetching: false,
    error: null,
    refetch: vi.fn(),
  }),
  useUpdateCommissionerSettings: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
  }),
}));

describe('CommissionerSettingsTab', () => {
  it('renders general settings controls and league cards', () => {
    render(<CommissionerSettingsTab />);

    expect(screen.getByRole('heading', { level: 3, name: 'Bulk League Settings' })).toBeInTheDocument();
    expect(screen.getByText('Best Ball League Alpha')).toBeInTheDocument();
    expect(screen.getByText('Lineup League Beta')).toBeInTheDocument();

    // Check Best Ball & Bench Lock notice
    expect(screen.getByText(/Best Ball & Bench Lock Shortcut/i)).toBeInTheDocument();

    // Check badges
    expect(screen.getByText('Best Ball')).toBeInTheDocument();
    expect(screen.getByText('Lineup')).toBeInTheDocument();
    expect(screen.getByText('Bench Lock: OFF')).toBeInTheDocument();
    expect(screen.getByText('Bench Lock: ON')).toBeInTheDocument();
  });

  it('filters leagues with search input and type pills', () => {
    render(<CommissionerSettingsTab />);

    // Filter to Best Ball only
    const bestBallPill = screen.getByRole('button', { name: /Best Ball \(1\)/i });
    fireEvent.click(bestBallPill);

    expect(screen.getByText('Best Ball League Alpha')).toBeInTheDocument();
    expect(screen.queryByText('Lineup League Beta')).not.toBeInTheDocument();

    // Filter to Lineup only
    const lineupPill = screen.getByRole('button', { name: /Lineup \(1\)/i });
    fireEvent.click(lineupPill);

    expect(screen.queryByText('Best Ball League Alpha')).not.toBeInTheDocument();
    expect(screen.getByText('Lineup League Beta')).toBeInTheDocument();
  });

  it('selects leagues and applies bench lock update', async () => {
    // Mock window.confirm
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(<CommissionerSettingsTab />);

    // Select all
    const selectAllBtn = screen.getByRole('button', { name: /Select All/i });
    fireEvent.click(selectAllBtn);

    expect(screen.getByText(/Apply to 2 Selected Leagues/i)).toBeInTheDocument();

    // Change Bench Drop Lock to Prevent Bench Drops (Locked = 1)
    const benchSelect = screen.getAllByRole('combobox')[0];
    fireEvent.change(benchSelect, { target: { value: '1' } });

    // Click Apply
    const applyBtn = screen.getByRole('button', { name: /Apply to 2 Selected Leagues/i });
    fireEvent.click(applyBtn);

    expect(confirmSpy).toHaveBeenCalled();
    expect(mockMutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({
        league_ids: ['l1', 'l2'],
        bench_lock: 1,
      })
    );

    confirmSpy.mockRestore();
  });
});
