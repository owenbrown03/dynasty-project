import type {
  Dispatch,
  SetStateAction,
} from 'react';
import { Filter } from 'lucide-react';

import type { ADPFilters } from '@/types';

import {
  ADP_LIMIT_OPTIONS,
  DEFAULT_ADP_FILTERS,
} from './adp.utils';

type FilterOption = {
  value: string;
  label: string;
};

interface AdpFiltersPanelProps {
  filters: ADPFilters;
  seasonOptions: FilterOption[];
  draftKindOptions: FilterOption[];
  qbFormatOptions: FilterOption[];
  tepOptions: FilterOption[];
  scoringOptions: FilterOption[];
  teamCountOptions: FilterOption[];
  setFilters: Dispatch<SetStateAction<ADPFilters>>;
  onCopyBoardLink: () => void;
  onResetBoardView: () => void;
  onApplyDateWindow: (days: number | null) => void;
}

export function AdpFiltersPanel({
  filters,
  seasonOptions,
  draftKindOptions,
  qbFormatOptions,
  tepOptions,
  scoringOptions,
  teamCountOptions,
  setFilters,
  onCopyBoardLink,
  onResetBoardView,
  onApplyDateWindow,
}: AdpFiltersPanelProps) {
  return (
    <section className="adp-filters-card">
      <div className="adp-filters-header">
        <div>
          <span className="adp-section-kicker">Filters</span>
          <h2>Draft sample controls</h2>
        </div>
        <div className="adp-filters-actions">
          <div className="adp-filters-note">
            <Filter size={16} />
            <span>Changing filters requeries the cached `/adp` dataset.</span>
          </div>
          <button
            type="button"
            className="site-button site-button-secondary"
            onClick={onCopyBoardLink}
          >
            Copy link
          </button>
          <button
            type="button"
            className="site-button site-button-secondary"
            onClick={onResetBoardView}
          >
            Reset board
          </button>
        </div>
      </div>

      <div className="adp-filters-grid">
        <label>
          <span>Season</span>
          <select
            value={filters.season ?? ''}
            onChange={(event) => {
              const value = event.target.value.trim();
              setFilters((current) => ({
                ...current,
                season: value || null,
              }));
            }}
          >
            {seasonOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Draft kind</span>
          <select
            value={filters.draft_kind ?? ''}
            onChange={(event) => {
              const value = event.target.value;
              setFilters((current) => ({
                ...current,
                draft_kind: value || null,
              }));
            }}
          >
            {draftKindOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>QB format</span>
          <select
            value={filters.qb_format ?? ''}
            onChange={(event) => {
              const value = event.target.value;
              setFilters((current) => ({
                ...current,
                qb_format: value || null,
              }));
            }}
          >
            {qbFormatOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>TE premium</span>
          <select
            value={filters.te_premium ?? ''}
            onChange={(event) => {
              const value = event.target.value;
              setFilters((current) => ({
                ...current,
                te_premium: value || null,
              }));
            }}
          >
            {tepOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Scoring</span>
          <select
            value={filters.scoring_format ?? ''}
            onChange={(event) => {
              const value = event.target.value;
              setFilters((current) => ({
                ...current,
                scoring_format: value || null,
              }));
            }}
          >
            {scoringOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Team count</span>
          <select
            value={filters.team_count?.toString() ?? ''}
            onChange={(event) => {
              const value = event.target.value;
              setFilters((current) => ({
                ...current,
                team_count: value ? Number(value) : null,
              }));
            }}
          >
            {teamCountOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Min draft count</span>
          <input
            type="number"
            min={1}
            max={999}
            value={filters.minimum_draft_count ?? 1}
            onChange={(event) => {
              const value = Number(event.target.value);
              setFilters((current) => ({
                ...current,
                minimum_draft_count: value,
              }));
            }}
          />
        </label>

        <label>
          <span>Row limit</span>
          <select
            value={String(filters.limit ?? DEFAULT_ADP_FILTERS.limit ?? 300)}
            onChange={(event) => {
              const value = Number(event.target.value);
              setFilters((current) => ({
                ...current,
                limit: value,
              }));
            }}
          >
            {ADP_LIMIT_OPTIONS.map((limit) => (
              <option key={limit} value={limit}>
                Top {limit}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Start date</span>
          <input
            type="date"
            value={filters.start_date ?? ''}
            onChange={(event) => {
              const value = event.target.value;
              setFilters((current) => ({
                ...current,
                start_date: value || null,
              }));
            }}
          />
        </label>

        <label>
          <span>End date</span>
          <input
            type="date"
            value={filters.end_date ?? ''}
            onChange={(event) => {
              const value = event.target.value;
              setFilters((current) => ({
                ...current,
                end_date: value || null,
              }));
            }}
          />
        </label>

        <div className="adp-filter-window">
          <span>Date presets</span>
          <div className="adp-filter-window-buttons">
            <button
              type="button"
              className="site-button site-button-secondary"
              onClick={() => {
                onApplyDateWindow(30);
              }}
            >
              Last 30d
            </button>
            <button
              type="button"
              className="site-button site-button-secondary"
              onClick={() => {
                onApplyDateWindow(60);
              }}
            >
              Last 60d
            </button>
            <button
              type="button"
              className="site-button site-button-secondary"
              onClick={() => {
                onApplyDateWindow(90);
              }}
            >
              Last 90d
            </button>
            <button
              type="button"
              className="site-button site-button-secondary"
              onClick={() => {
                onApplyDateWindow(null);
              }}
            >
              All time
            </button>
          </div>
        </div>

      </div>
    </section>
  );
}
