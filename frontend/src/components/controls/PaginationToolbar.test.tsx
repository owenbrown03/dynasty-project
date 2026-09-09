import {
  fireEvent,
  render,
  screen,
} from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { PaginationToolbar } from './PaginationToolbar';

describe('PaginationToolbar', () => {
  it('emits page and page-size changes', () => {
    const onPageChange = vi.fn();
    const onPageSizeChange = vi.fn();

    render(
      <PaginationToolbar
        page={2}
        pageSize={50}
        totalPages={4}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
      />,
    );

    expect(screen.getByText('Page 2 of 4')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Previous' }));
    fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    fireEvent.change(screen.getByLabelText('Rows'), {
      target: {
        value: '100',
      },
    });

    expect(onPageChange).toHaveBeenNthCalledWith(1, 1);
    expect(onPageChange).toHaveBeenNthCalledWith(2, 3);
    expect(onPageSizeChange).toHaveBeenCalledWith(100);
  });

  it('applies custom className to the root container', () => {
    const { container } = render(
      <PaginationToolbar
        page={1}
        pageSize={50}
        totalPages={1}
        onPageChange={vi.fn()}
        onPageSizeChange={vi.fn()}
        className="custom-toolbar-class"
      />,
    );

    expect(container.firstElementChild).toHaveClass('available-pagination-toolbar');
    expect(container.firstElementChild).toHaveClass('custom-toolbar-class');
  });
});
