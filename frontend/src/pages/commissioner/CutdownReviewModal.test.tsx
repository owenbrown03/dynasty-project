import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { CutdownReviewModal, type CutdownRosterPreview } from './CutdownReviewModal';

afterEach(() => {
  cleanup();
});

describe('CutdownReviewModal', () => {
  const samplePreviews: CutdownRosterPreview[] = [
    {
      leagueId: 'l-1',
      leagueName: 'The League',
      rosterId: 1,
      ownerName: 'Manager Dave',
      overLimitCount: 2,
      drops: [
        {
          player_id: 'p-1',
          name: 'Lowest Value Player',
          position: 'RB',
          team: 'KC',
          ktc_value: 120,
        },
        {
          player_id: 'p-2',
          name: 'Backup Kicker',
          position: 'K',
          team: 'BAL',
          ktc_value: 0,
        },
      ],
    },
  ];

  it('renders preview modal with owner, league, and player details including KTC values', () => {
    const onConfirm = vi.fn();
    const onClose = vi.fn();

    render(
      <CutdownReviewModal
        previews={samplePreviews}
        submitting={false}
        results={[]}
        error={null}
        onClose={onClose}
        onConfirm={onConfirm}
      />,
    );

    expect(screen.getByText('Review Forced Drops')).toBeInTheDocument();
    expect(screen.getByText('Manager Dave')).toBeInTheDocument();
    expect(screen.getByText('The League')).toBeInTheDocument();
    expect(screen.getByText('Lowest Value Player')).toBeInTheDocument();
    expect(screen.getByText('120')).toBeInTheDocument();
    expect(screen.getByText('Backup Kicker')).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();

    const confirmBtn = screen.getByRole('button', { name: /Confirm Force Drop/i });
    expect(confirmBtn).toBeEnabled();
    fireEvent.click(confirmBtn);
    expect(onConfirm).toHaveBeenCalledTimes(1);

    const cancelBtn = screen.getByRole('button', { name: /Cancel/i });
    fireEvent.click(cancelBtn);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('renders results view after drops are executed', () => {
    const onClose = vi.fn();

    render(
      <CutdownReviewModal
        previews={samplePreviews}
        submitting={false}
        results={[
          {
            league_id: 'l-1',
            roster_id: 1,
            action: 'force_drop',
            success: true,
            details: 'Dropped 2 players successfully',
            error: null,
          },
        ]}
        error={null}
        onClose={onClose}
        onConfirm={vi.fn()}
      />,
    );

    expect(screen.getByText('Cutdown Results')).toBeInTheDocument();
    expect(screen.getByText('Dropped 2 players successfully')).toBeInTheDocument();

    const doneBtn = screen.getByRole('button', { name: /Done/i });
    fireEvent.click(doneBtn);
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
