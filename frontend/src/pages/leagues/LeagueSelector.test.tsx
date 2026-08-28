import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import type { LeagueSelectorItem } from '@/types';
import { LeagueSelector } from './LeagueSelector';

afterEach(() => {
  cleanup();
});

const mockLeagues: LeagueSelectorItem[] = [
  {
    league_id: 'league-1',
    league_name: 'Dynasty Championship',
    season: '2026',
    is_hidden: false,
    is_focused: true,
  },
  {
    league_id: 'league-2',
    league_name: 'Rebuilder League',
    season: '2025',
    is_hidden: true,
    is_focused: false,
  },
  {
    league_id: 'league-3',
    league_name: 'Standard League',
    season: null,
    is_hidden: false,
    is_focused: false,
  },
];

describe('LeagueSelector', () => {
  it('renders select dropdown with default option and league options', () => {
    render(
      <LeagueSelector
        leagues={mockLeagues}
        selectedLeague="league-1"
        onSelect={vi.fn()}
      />,
    );

    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();
    expect(select).toHaveValue('league-1');

    expect(screen.getByRole('option', { name: 'Select League' })).toBeInTheDocument();
    expect(
      screen.getByRole('option', { name: /★ Dynasty Championship - 2026/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('option', { name: /Rebuilder League \(hidden\) - 2025/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('option', { name: 'Standard League' }),
    ).toBeInTheDocument();
  });

  it('triggers onSelect callback when user selects a league', () => {
    const onSelect = vi.fn();
    render(
      <LeagueSelector
        leagues={mockLeagues}
        selectedLeague=""
        onSelect={onSelect}
      />,
    );

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'league-2' } });

    expect(onSelect).toHaveBeenCalledWith('league-2');
  });
});
