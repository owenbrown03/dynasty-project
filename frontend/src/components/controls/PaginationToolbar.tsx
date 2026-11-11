import './PaginationToolbar.css';

import type { ReactNode } from 'react';
import { scrollToPageTop } from '@/utils/scroll';

interface PaginationToolbarProps {
  page: number;
  pageSize: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  pageSizeOptions?: number[];
  leadingControls?: ReactNode;
  className?: string;
  scrollToTop?: boolean;
}

export function PaginationToolbar({
  page,
  pageSize,
  totalPages,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [
    50,
    100,
    150,
  ],
  leadingControls,
  className,
  scrollToTop = true,
}: PaginationToolbarProps) {
  const rootClassName = className
    ? `available-pagination-toolbar ${className}`
    : 'available-pagination-toolbar';

  const handlePageChange = (nextPage: number) => {
    onPageChange(nextPage);
    if (scrollToTop) {
      scrollToPageTop();
    }
  };

  const handlePageSizeChange = (nextPageSize: number) => {
    onPageSizeChange(nextPageSize);
    if (scrollToTop) {
      scrollToPageTop();
    }
  };

  return (
    <div className={rootClassName}>
      {leadingControls}

      <label className="available-page-size-selector">
        <span>Rows</span>

        <select
          value={pageSize}
          onChange={(event) => {
            handlePageSizeChange(
              Number(
                event.target.value,
              ),
            );
          }}
        >
          {pageSizeOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>

      <div className="available-pagination-status">
        Page {page}
        {' of '}
        {totalPages}
      </div>

      <div className="available-pagination-actions">
        <button
          type="button"
          className="button-secondary"
          disabled={page <= 1}
          onClick={() => {
            handlePageChange(page - 1);
          }}
        >
          Previous
        </button>

        <button
          type="button"
          className="button-secondary"
          disabled={page >= totalPages}
          onClick={() => {
            handlePageChange(page + 1);
          }}
        >
          Next
        </button>
      </div>
    </div>
  );
}
