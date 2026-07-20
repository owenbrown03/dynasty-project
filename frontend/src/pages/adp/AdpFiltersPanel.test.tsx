import {
  fireEvent,
  render,
  screen,
} from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { ADPFilters } from '@/types';

import { AdpFiltersPanel } from './AdpFiltersPanel';

const filters: ADPFilters = {
  season: '2026',
  draft_kind: 'startup',
  qb_format: 'superflex',
  te_premium: null,
  scoring_format: null,
  team_count: 12,
  minimum_draft_count: 5,
  limit: 300,
  start_date: '2026-05-01',
  end_date: '2026-07-20',
};

const baseOptions = [{ value: '', label: 'All' }];

describe('AdpFiltersPanel', () => {
  it('emits filter updates and action callbacks', () => {
    const setFilters = vi.fn();
    const onCopyBoardLink = vi.fn();
    const onResetBoardView = vi.fn();
    const onApplyDateWindow = vi.fn();

    render(
      <AdpFiltersPanel
        filters={filters}
        seasonOptions={[
          { value: '2026', label: '2026' },
          { value: '2025', label: '2025' },
        ]}
        draftKindOptions={[
          { value: 'startup', label: 'Startup' },
          { value: 'rookie', label: 'Rookie' },
        ]}
        qbFormatOptions={[
          { value: 'superflex', label: 'Superflex' },
          { value: 'one_qb', label: '1QB' },
        ]}
        tepOptions={baseOptions}
        scoringOptions={baseOptions}
        teamCountOptions={[
          { value: '', label: 'All teams' },
          { value: '12', label: '12 teams' },
        ]}
        setFilters={setFilters}
        onCopyBoardLink={onCopyBoardLink}
        onResetBoardView={onResetBoardView}
        onApplyDateWindow={onApplyDateWindow}
      />,
    );

    fireEvent.change(screen.getByLabelText('Season'), {
      target: { value: '2025' },
    });
    expect(setFilters).toHaveBeenCalled();
    expect(setFilters.mock.calls.at(-1)?.[0](filters)).toMatchObject({
      season: '2025',
    });

    fireEvent.change(screen.getByLabelText('QB format'), {
      target: { value: 'one_qb' },
    });
    expect(setFilters.mock.calls.at(-1)?.[0](filters)).toMatchObject({
      qb_format: 'one_qb',
    });

    fireEvent.change(screen.getByLabelText('Team count'), {
      target: { value: '' },
    });
    expect(setFilters.mock.calls.at(-1)?.[0](filters)).toMatchObject({
      team_count: null,
    });

    fireEvent.click(screen.getByRole('button', { name: 'Copy link' }));
    fireEvent.click(screen.getByRole('button', { name: 'Reset board' }));
    fireEvent.click(screen.getByRole('button', { name: 'Last 30d' }));
    fireEvent.click(screen.getByRole('button', { name: 'All time' }));

    expect(onCopyBoardLink).toHaveBeenCalledTimes(1);
    expect(onResetBoardView).toHaveBeenCalledTimes(1);
    expect(onApplyDateWindow).toHaveBeenCalledWith(30);
    expect(onApplyDateWindow).toHaveBeenCalledWith(null);
  });
});
