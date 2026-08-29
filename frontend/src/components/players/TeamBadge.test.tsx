import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { TeamBadge } from './TeamBadge';

afterEach(() => {
  cleanup();
});

describe('TeamBadge', () => {
  it('renders team name and Sleeper CDN logo for valid NFL teams', () => {
    render(<TeamBadge team="BAL" size="sm" />);
    expect(screen.getByText('BAL')).toBeInTheDocument();

    const img = screen.getByRole('img', { name: 'BAL logo' });
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('src', 'https://sleepercdn.com/images/team_logos/nfl/bal.png');
  });

  it('renders lowercase team abbreviations correctly', () => {
    render(<TeamBadge team="kc" size="md" />);
    expect(screen.getByText('kc')).toBeInTheDocument();

    const img = screen.getByRole('img', { name: 'kc logo' });
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('src', 'https://sleepercdn.com/images/team_logos/nfl/kc.png');
  });

  it('renders fallback text without logo for FA or null team', () => {
    render(<TeamBadge team={null} fallbackText="FA" />);
    expect(screen.getByText('FA')).toBeInTheDocument();
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
  });
});
