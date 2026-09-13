import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { CommissionerWaiversTab } from './CommissionerWaiversTab';

afterEach(() => {
  cleanup();
});

const mockMutateAsync = vi.fn();

vi.mock('@/hooks/sleeper/useUsers', () => ({
  useCommissionerWaiversOverview: () => ({
    data: [
      {
        league_id: 'l1',
        league_name: 'League Alpha',
        avatar: null,
        total_rosters: 12,
        daily_waivers: 1,
        daily_waivers_hour: 0,
        daily_waivers_days: 5461,
        daily_waivers_days_b4: '1111111',
        waiver_type: 2,
        schedule: [
          { day: 'Sunday', setting: 1 },
          { day: 'Monday', setting: 1 },
          { day: 'Tuesday', setting: 1 },
          { day: 'Wednesday', setting: 1 },
          { day: 'Thursday', setting: 1 },
          { day: 'Friday', setting: 1 },
          { day: 'Saturday', setting: 1 },
        ],
      },
      {
        league_id: 'l2',
        league_name: 'League Beta',
        avatar: null,
        total_rosters: 10,
        daily_waivers: 0,
        daily_waivers_hour: 9,
        daily_waivers_days: 10736,
        daily_waivers_days_b4: '2213300',
        waiver_type: 2,
        schedule: [
          { day: 'Sunday', setting: 0 },
          { day: 'Monday', setting: 2 },
          { day: 'Tuesday', setting: 2 },
          { day: 'Wednesday', setting: 1 },
          { day: 'Thursday', setting: 3 },
          { day: 'Friday', setting: 3 },
          { day: 'Saturday', setting: 0 },
        ],
      },
    ],
    isLoading: false,
    isFetching: false,
    error: null,
    refetch: vi.fn(),
  }),
  useUpdateCommissionerWaivers: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
  }),
}));

describe('CommissionerWaiversTab', () => {
  it('renders schedule controls and league cards', () => {
    render(<CommissionerWaiversTab />);

    expect(screen.getByText('Custom Waivers Schedule')).toBeInTheDocument();
    expect(screen.getByText('League Alpha')).toBeInTheDocument();
    expect(screen.getByText('League Beta')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Select All/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Select None/i })).toBeInTheDocument();
  });

  it('selects and deselects leagues using Select All and Select None', () => {
    render(<CommissionerWaiversTab />);

    const selectAllBtn = screen.getByRole('button', { name: /Select All/i });
    fireEvent.click(selectAllBtn);

    expect(screen.getByText(/Apply to 2 Selected Leagues/i)).toBeInTheDocument();

    const selectNoneBtn = screen.getByRole('button', { name: /Select None/i });
    fireEvent.click(selectNoneBtn);

    expect(screen.getByText(/Apply to 0 Selected Leagues/i)).toBeInTheDocument();
  });

  it('filters leagues with search input', () => {
    render(<CommissionerWaiversTab />);

    const searchInput = screen.getByPlaceholderText(/Search commissioner leagues/i);
    fireEvent.change(searchInput, { target: { value: 'Beta' } });

    expect(screen.queryByText('League Alpha')).not.toBeInTheDocument();
    expect(screen.getByText('League Beta')).toBeInTheDocument();
  });
});
