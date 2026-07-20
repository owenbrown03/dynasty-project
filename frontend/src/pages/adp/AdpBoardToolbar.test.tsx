import {
  fireEvent,
  render,
  screen,
} from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { AdpBoardToolbar } from './AdpBoardToolbar';

describe('AdpBoardToolbar', () => {
  it('emits board filter and sorting changes', () => {
    const onPlayerSearchChange = vi.fn();
    const onPositionFilterChange = vi.fn();
    const onViewModeChange = vi.fn();
    const onDraftOrderModeChange = vi.fn();
    const onSortColumnChange = vi.fn();
    const onSortDirectionChange = vi.fn();

    render(
      <AdpBoardToolbar
        playerSearch=""
        positionFilter=""
        positionOptions={['QB', 'RB']}
        viewMode="board"
        draftOrderMode="snake"
        sortColumn="overall_adp"
        sortDirection="asc"
        visibleCount={42}
        secondaryCount={12}
        onPlayerSearchChange={onPlayerSearchChange}
        onPositionFilterChange={onPositionFilterChange}
        onViewModeChange={onViewModeChange}
        onDraftOrderModeChange={onDraftOrderModeChange}
        onSortColumnChange={onSortColumnChange}
        onSortDirectionChange={onSortDirectionChange}
      />,
    );

    expect(screen.getByText('42 / 12')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Search players'), {
      target: {
        value: 'Josh',
      },
    });
    fireEvent.change(screen.getByLabelText('Position'), {
      target: {
        value: 'QB',
      },
    });
    fireEvent.change(screen.getByLabelText('Layout'), {
      target: {
        value: 'table',
      },
    });
    fireEvent.change(screen.getByLabelText('Draft order'), {
      target: {
        value: 'linear',
      },
    });
    fireEvent.change(screen.getByLabelText('Board order'), {
      target: {
        value: 'name',
      },
    });
    fireEvent.change(screen.getByLabelText('Direction'), {
      target: {
        value: 'desc',
      },
    });

    expect(onPlayerSearchChange).toHaveBeenCalledWith('Josh');
    expect(onPositionFilterChange).toHaveBeenCalledWith('QB');
    expect(onViewModeChange).toHaveBeenCalledWith('table');
    expect(onDraftOrderModeChange).toHaveBeenCalledWith('linear');
    expect(onSortColumnChange).toHaveBeenCalledWith('name');
    expect(onSortDirectionChange).toHaveBeenCalledWith('desc');
  });
});
