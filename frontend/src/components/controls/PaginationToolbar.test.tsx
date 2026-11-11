import {
  cleanup,
  fireEvent,
  render,
  screen,
} from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { PaginationToolbar } from './PaginationToolbar';

describe('PaginationToolbar', () => {
  afterEach(() => {
    cleanup();
  });
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

  it('scrolls to top on page change by default', async () => {
    const scrollModule = await import('@/utils/scroll');
    const scrollSpy = vi.spyOn(scrollModule, 'scrollToPageTop');

    render(
      <PaginationToolbar
        page={2}
        pageSize={50}
        totalPages={4}
        onPageChange={vi.fn()}
        onPageSizeChange={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    expect(scrollSpy).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button', { name: 'Previous' }));
    expect(scrollSpy).toHaveBeenCalledTimes(2);

    fireEvent.change(screen.getByLabelText('Rows'), {
      target: { value: '100' },
    });
    expect(scrollSpy).toHaveBeenCalledTimes(3);

    scrollSpy.mockRestore();
  });

  it('does not scroll to top when scrollToTop is false', async () => {
    const scrollModule = await import('@/utils/scroll');
    const scrollSpy = vi.spyOn(scrollModule, 'scrollToPageTop');

    render(
      <PaginationToolbar
        page={2}
        pageSize={50}
        totalPages={4}
        onPageChange={vi.fn()}
        onPageSizeChange={vi.fn()}
        scrollToTop={false}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    expect(scrollSpy).not.toHaveBeenCalled();

    scrollSpy.mockRestore();
  });
});
