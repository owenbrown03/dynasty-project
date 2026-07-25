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

import type { PersonalValueSearchResult } from '@/types';

import { MyValuesSearchCard } from './MyValuesSearchCard';

afterEach(() => {
  cleanup();
});

const result: PersonalValueSearchResult = {
  player_id: '1',
  name: 'Josh Allen',
  position: 'QB',
  team: 'BUF',
  age: 30,
  underdog_position_rank: 'QB1',
  ktc_value: 10000,
  fc_value: 9500,
  adp_value: 1.2,
  dynasty_roster_war: 8.5,
};

describe('MyValuesSearchCard', () => {
  it('shows helper copy before search is enabled', () => {
    render(
      <MyValuesSearchCard
        searchTerm=""
        searchEnabled={false}
        loading={false}
        fetching={false}
        results={[]}
        onSearchTermChange={vi.fn()}
        onSelectPlayer={vi.fn()}
      />,
    );

    expect(
      screen.getByText(/Search at least two characters/),
    ).toBeInTheDocument();
  });

  it('delegates search input changes and result selection', () => {
    const onSearchTermChange = vi.fn();
    const onSelectPlayer = vi.fn();

    render(
      <MyValuesSearchCard
        searchTerm="Josh"
        searchEnabled
        loading={false}
        fetching={false}
        results={[result]}
        onSearchTermChange={onSearchTermChange}
        onSelectPlayer={onSelectPlayer}
      />,
    );

    fireEvent.change(screen.getByLabelText('Player search'), {
      target: { value: 'Drake' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Josh Allen/ }));

    expect(onSearchTermChange).toHaveBeenCalledWith('Drake');
    expect(onSelectPlayer).toHaveBeenCalledWith('1');
    expect(screen.getByText('KTC 10,000')).toBeInTheDocument();
    expect(screen.getByText('WAR 8.50')).toBeInTheDocument();
  });

  it('shows loading state while searching', () => {
    render(
      <MyValuesSearchCard
        searchTerm="Jo"
        searchEnabled
        loading
        fetching={false}
        results={[result]}
        onSearchTermChange={vi.fn()}
        onSelectPlayer={vi.fn()}
      />,
    );

    expect(screen.getByText('Searching')).toBeInTheDocument();
    expect(screen.queryByText('Josh Allen')).not.toBeInTheDocument();
  });
});
