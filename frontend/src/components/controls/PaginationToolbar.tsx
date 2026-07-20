import './PaginationToolbar.css';

import type { ReactNode } from 'react';

interface PaginationToolbarProps {
  page: number;
  pageSize: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  pageSizeOptions?: number[];
  leadingControls?: ReactNode;
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
}: PaginationToolbarProps) {
  return (
    <div className="available-pagination-toolbar">
      {leadingControls}

      <label className="available-page-size-selector">
        <span>Rows</span>

        <select
          value={pageSize}
          onChange={(event) => {
            onPageSizeChange(
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
            onPageChange(page - 1);
          }}
        >
          Previous
        </button>

        <button
          type="button"
          className="button-secondary"
          disabled={page >= totalPages}
          onClick={() => {
            onPageChange(page + 1);
          }}
        >
          Next
        </button>
      </div>
    </div>
  );
}
