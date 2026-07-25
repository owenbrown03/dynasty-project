import {
  cleanup,
  fireEvent,
  render,
  screen,
} from '@testing-library/react';
import {
  afterEach,
  describe,
  expect,
  it,
  vi,
} from 'vitest';

import type {
  PersonalValueMetrics,
  PersonalValuePoolItem,
} from '@/types';

import { MyValuesPoolPanel } from './MyValuesPoolPanel';

afterEach(() => {
  cleanup();
});

const metrics = (
  dynastyRosterWar: number | null,
): PersonalValueMetrics => ({
  redraft_starter_war: null,
  redraft_roster_war: null,
  dynasty_starter_war: null,
  dynasty_roster_war: dynastyRosterWar,
});

function poolItem(
  playerId: string,
  name: string,
): PersonalValuePoolItem {
  return {
    player: {
      player_id: playerId,
      name,
      position: 'QB',
      team: 'BUF',
      age: 29,
      underdog_position_rank: 'QB1',
      ktc_value: 10000,
      fc_value: 9500,
      adp_value: 1.2,
    },
    market_values: metrics(7),
    custom_values: metrics(8.5),
    delta_values: metrics(1.5),
    is_customized: playerId === '1',
  };
}

describe('MyValuesPoolPanel', () => {
  it('renders the projection pool table and delegates row selection', () => {
    const onSelectPlayer = vi.fn();

    render(
      <MyValuesPoolPanel
        leagueName="Best Ball"
        fetching={false}
        loading={false}
        searchSort="my_war"
        sortDirection="desc"
        tableFilters={[{ id: 1, column: 'player', operator: 'contains', value: '' }]}
        filteredPoolItems={[poolItem('1', 'Josh Allen')]}
        filteredPoolCount={1}
        pageSummaryMetric="My dynasty roster WAR"
        selectedPlayerId="1"
        onSearchSortChange={vi.fn()}
        onSortDirectionChange={vi.fn()}
        onAddTableFilter={vi.fn()}
        onUpdateTableFilter={vi.fn()}
        onRemoveTableFilter={vi.fn()}
        onHeaderSort={vi.fn()}
        onSelectPlayer={onSelectPlayer}
      />,
    );

    expect(screen.getByText('Best Ball')).toBeInTheDocument();
    expect(screen.getByText('Josh Allen')).toBeInTheDocument();
    expect(screen.getByText('Customized')).toBeInTheDocument();
    expect(screen.getByText('8.50')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Josh Allen'));
    expect(onSelectPlayer).toHaveBeenCalledWith('1');
  });

  it('delegates sort and filter control changes', () => {
    const onSearchSortChange = vi.fn();
    const onSortDirectionChange = vi.fn();
    const onAddTableFilter = vi.fn();
    const onUpdateTableFilter = vi.fn();
    const onRemoveTableFilter = vi.fn();
    const onHeaderSort = vi.fn();

    render(
      <MyValuesPoolPanel
        leagueName="Best Ball"
        fetching={false}
        loading={false}
        searchSort="my_war"
        sortDirection="desc"
        tableFilters={[{ id: 1, column: 'player', operator: 'contains', value: '' }]}
        filteredPoolItems={[poolItem('1', 'Josh Allen')]}
        filteredPoolCount={1}
        pageSummaryMetric="My dynasty roster WAR"
        selectedPlayerId=""
        onSearchSortChange={onSearchSortChange}
        onSortDirectionChange={onSortDirectionChange}
        onAddTableFilter={onAddTableFilter}
        onUpdateTableFilter={onUpdateTableFilter}
        onRemoveTableFilter={onRemoveTableFilter}
        onHeaderSort={onHeaderSort}
        onSelectPlayer={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByLabelText('Sort table by'), {
      target: { value: 'ktc' },
    });
    fireEvent.change(screen.getByLabelText('Direction'), {
      target: { value: 'asc' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Add filter' }));
    fireEvent.change(screen.getByDisplayValue('Player'), {
      target: { value: 'team' },
    });
    fireEvent.change(screen.getByPlaceholderText('Filter value'), {
      target: { value: 'buf' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Remove' }));
    fireEvent.click(screen.getByRole('button', { name: 'KTC' }));

    expect(onSearchSortChange).toHaveBeenCalledWith('ktc');
    expect(onSortDirectionChange).toHaveBeenCalledWith('asc');
    expect(onAddTableFilter).toHaveBeenCalledTimes(1);
    expect(onUpdateTableFilter).toHaveBeenCalledWith(1, { column: 'team' });
    expect(onUpdateTableFilter).toHaveBeenCalledWith(1, { value: 'buf' });
    expect(onRemoveTableFilter).toHaveBeenCalledWith(1);
    expect(onHeaderSort).toHaveBeenCalledWith('ktc');
  });

  it('shows loading state instead of table rows while loading', () => {
    render(
      <MyValuesPoolPanel
        leagueName="Best Ball"
        fetching
        loading
        searchSort="my_war"
        sortDirection="desc"
        tableFilters={[]}
        filteredPoolItems={[poolItem('1', 'Josh Allen')]}
        filteredPoolCount={1}
        pageSummaryMetric="My dynasty roster WAR"
        selectedPlayerId=""
        onSearchSortChange={vi.fn()}
        onSortDirectionChange={vi.fn()}
        onAddTableFilter={vi.fn()}
        onUpdateTableFilter={vi.fn()}
        onRemoveTableFilter={vi.fn()}
        onHeaderSort={vi.fn()}
        onSelectPlayer={vi.fn()}
      />,
    );

    expect(screen.getByText('Refreshing')).toBeInTheDocument();
    expect(
      screen.getByText('Building personal value pool...'),
    ).toBeInTheDocument();
    expect(screen.queryByText('Josh Allen')).not.toBeInTheDocument();
  });
});
