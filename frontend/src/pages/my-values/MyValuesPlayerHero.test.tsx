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

import type { PersonalValuePlayer } from '@/types';
import { MyValuesPlayerHero } from './MyValuesPlayerHero';

const player: PersonalValuePlayer = {
  player_id: '9999',
  name: 'Josh Downs',
  position: 'WR',
  team: 'IND',
  age: 24.9,
  underdog_position_rank: 'WR48',
  ktc_value: 2500,
  fc_value: 1800,
  adp_value: 102.4,
};

afterEach(() => {
  cleanup();
});

describe('MyValuesPlayerHero', () => {
  it('renders player context and delegates actions', () => {
    const onReset = vi.fn();
    const onSave = vi.fn();

    render(
      <MyValuesPlayerHero
        player={player}
        playerInPool
        saving={false}
        onReset={onReset}
        onSave={onSave}
      />,
    );

    expect(screen.getByText('Josh Downs')).toBeInTheDocument();
    expect(screen.getByText('WR')).toBeInTheDocument();
    expect(screen.getByText('IND')).toBeInTheDocument();
    expect(screen.getByText('Age 24.9')).toBeInTheDocument();
    expect(screen.getByText('WR48')).toBeInTheDocument();
    expect(screen.getByText('KTC 2,500')).toBeInTheDocument();
    expect(screen.getByText('FC 1,800')).toBeInTheDocument();
    expect(screen.getByText('ADP 102')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Reset view' }));
    fireEvent.click(screen.getByRole('button', { name: 'Save projections' }));

    expect(onReset).toHaveBeenCalledTimes(1);
    expect(onSave).toHaveBeenCalledTimes(1);
  });

  it('shows the saving state and disables actions', () => {
    render(
      <MyValuesPlayerHero
        player={player}
        playerInPool={false}
        saving
        onReset={vi.fn()}
        onSave={vi.fn()}
      />,
    );

    expect(screen.getByText('This player will join your saved projection pool once you save a custom projection.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Reset view' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Saving...' })).toBeDisabled();
  });
});
