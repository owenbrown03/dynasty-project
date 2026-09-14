import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { CommissionerWaiversTab } from './CommissionerWaiversTab';

afterEach(() => {
  cleanup();
});

const mockMutateAsync = vi.fn().mockResolvedValue({ successful_leagues: 2, results: [] });
const mockSavePreset = vi.fn().mockResolvedValue({});
const mockResetPreset = vi.fn().mockResolvedValue({});

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
    league_name: 'League Alpha',
    avatar: null,
    total_rosters: 12,
    daily_waivers: 1,
    daily_waivers_hour: 0,
    daily_waivers_days: 5461,
    daily_waivers_days_b4: '1111111',
    waiver_type: 2,
    waiver_clear_days: 2,
    waiver_day_of_week: 2,
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
    waiver_clear_days: 1,
    waiver_day_of_week: 0,
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
];

const mockPresetData = {
  sunday_to_saturday_settings: [3, 0, 1, 1, 3, 3, 3],
  daily_waivers_hour: null,
  daily_waivers: 1,
  is_custom: true,
};

vi.mock('@/hooks/sleeper/useUsers', () => ({
  useCommissionerWaiversOverview: () => ({
    data: mockOverviewData,
    isLoading: false,
    isFetching: false,
    error: null,
    refetch: vi.fn(),
  }),
  useUpdateCommissionerWaivers: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
  }),
  useCommissionerWaiversPreset: (presetType = 'inseason') => ({
    data: presetType === 'offseason'
      ? { ...mockPresetData, sunday_to_saturday_settings: [2, 2, 2, 1, 2, 2, 2] }
      : mockPresetData,
    isLoading: false,
  }),
  useSaveCommissionerWaiversPreset: () => ({
    mutateAsync: mockSavePreset,
    isPending: false,
  }),
  useResetCommissionerWaiversPreset: () => ({
    mutateAsync: mockResetPreset,
    isPending: false,
  }),
}));

describe('CommissionerWaiversTab', () => {
  it('renders schedule controls and league cards', () => {
    render(<CommissionerWaiversTab />);

    expect(screen.getByRole('heading', { level: 3, name: 'Allow Custom Daily Waivers' })).toBeInTheDocument();
    expect(screen.getByText('League Alpha')).toBeInTheDocument();
    expect(screen.getByText('League Beta')).toBeInTheDocument();
    expect(screen.getByText(/After Games: None/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Select All/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Select None/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Standard In-Season/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Standard Off-Season/i })).toBeInTheDocument();

    // Check After Games Waivers Clear dropdown options include None
    const noneOption = screen.getByRole('option', { name: 'None' });
    expect(noneOption).toBeInTheDocument();
    expect((noneOption as HTMLOptionElement).value).toBe('0');

    // Check preset match badge on League Alpha
    expect(screen.getByTitle('League schedule matches All Waivers preset')).toBeInTheDocument();
  });

  it('opens and closes the Allow Custom Daily Waivers info modal', () => {
    render(<CommissionerWaiversTab />);

    const infoBtn = screen.getByRole('button', { name: /Allow Custom Daily Waivers Information/i });
    fireEvent.click(infoBtn);

    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeInTheDocument();
    expect(
      screen.getByText(/Specify custom times for waivers to clear/i)
    ).toBeInTheDocument();
    expect(dialog).toHaveTextContent(/After Games Waivers Clear/i);

    // Close via Got It button
    const closeBtn = screen.getByRole('button', { name: /Got It/i });
    fireEvent.click(closeBtn);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
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

  it('handles saving and resetting custom in-season and off-season presets', async () => {
    render(<CommissionerWaiversTab />);

    // Custom badges should be shown because is_custom is true
    expect(screen.getAllByText('Customized').length).toBeGreaterThanOrEqual(1);

    // Click Save as In-Season
    const saveInSeasonBtn = screen.getByRole('button', { name: /Save as In-Season/i });
    fireEvent.click(saveInSeasonBtn);
    expect(mockSavePreset).toHaveBeenCalledWith(
      expect.objectContaining({
        sunday_to_saturday_settings: [3, 0, 1, 1, 3, 3, 3],
        presetType: 'inseason',
      })
    );

    // Click Save as Off-Season
    const saveOffSeasonBtn = screen.getByRole('button', { name: /Save as Off-Season/i });
    fireEvent.click(saveOffSeasonBtn);
    expect(mockSavePreset).toHaveBeenCalledWith(
      expect.objectContaining({
        presetType: 'offseason',
      })
    );

    // Click Reset to Default on In-Season
    const resetBtns = screen.getAllByRole('button', { name: /Reset to Default/i });
    fireEvent.click(resetBtns[0]);
    expect(mockResetPreset).toHaveBeenCalledWith('inseason');

    // Click Reset to Default on Off-Season
    fireEvent.click(resetBtns[1]);
    expect(mockResetPreset).toHaveBeenCalledWith('offseason');
  });
});


