import type {
  ADPDistributionItem,
  ADPSample,
} from '@/types';

import {
  formatDataSource,
  formatDateTime,
} from './adp.utils';

type SummaryCard = {
  label: string;
  value: string;
};

type DistributionGroup = {
  label: string;
  rows: ADPDistributionItem[];
  render: (row: ADPDistributionItem) => string;
};

type SampleStrength = {
  tone: string;
  title: string;
  body: string;
};

interface AdpSamplePanelsProps {
  sample: ADPSample | null | undefined;
  sampleStrength: SampleStrength;
  activeFilterPills: string[];
  corpusHealthCards: SummaryCard[];
  reportDistributionGroups: DistributionGroup[];
  sampleCompositionGroups: DistributionGroup[];
}

function SummaryGrid({
  cards,
}: {
  cards: SummaryCard[];
}) {
  return (
    <div className="adp-summary-grid">
      {cards.map((card) => (
        <article key={card.label} className="adp-summary-card">
          <span>{card.label}</span>
          <strong>{card.value}</strong>
        </article>
      ))}
    </div>
  );
}

function DistributionGrid({
  groups,
  emptyLabel,
  rowLimit,
}: {
  groups: DistributionGroup[];
  emptyLabel: string;
  rowLimit?: number;
}) {
  return (
    <div className="adp-composition-grid">
      {groups.map((group) => (
        <article key={group.label} className="adp-composition-group">
          <span>{group.label}</span>
          <div className="adp-composition-list">
            {group.rows.length ? group.rows.slice(0, rowLimit).map((row) => (
              <div key={`${group.label}-${row.key}`} className="adp-composition-pill">
                <strong>{group.render(row)}</strong>
                <small>{row.count.toLocaleString()} drafts</small>
              </div>
            )) : (
              <div className="adp-composition-empty">{emptyLabel}</div>
            )}
          </div>
        </article>
      ))}
    </div>
  );
}

export function AdpSamplePanels({
  sample,
  sampleStrength,
  activeFilterPills,
  corpusHealthCards,
  reportDistributionGroups,
  sampleCompositionGroups,
}: AdpSamplePanelsProps) {
  const sampleCards: SummaryCard[] = [
    {
      label: 'Qualified drafts',
      value: sample?.draft_count.toLocaleString() ?? '0',
    },
    {
      label: 'Qualified picks',
      value: sample?.pick_count.toLocaleString() ?? '0',
    },
    {
      label: 'Earliest draft',
      value: formatDateTime(sample?.earliest_draft_at ?? null),
    },
    {
      label: 'Latest draft',
      value: formatDateTime(sample?.latest_draft_at ?? null),
    },
    {
      label: 'Board source',
      value: formatDataSource(sample?.data_source),
    },
  ];

  return (
    <>
      <SummaryGrid cards={sampleCards} />

      <section className="adp-bias-note">
        <span className="adp-section-kicker">Sample note</span>
        <p>
          This board reflects drafts discovered through your Sleeper graph, not a random sample of all Sleeper drafts.
          Use the draft count, pick count, and date window to judge how representative each filter slice is.
        </p>
      </section>

      <section className={`adp-sample-health adp-sample-health-${sampleStrength.tone}`}>
        <span className="adp-section-kicker">Sample strength</span>
        <strong>{sampleStrength.title}</strong>
        <p>{sampleStrength.body}</p>
      </section>

      <section className="adp-active-filters">
        <span className="adp-section-kicker">Current slice</span>
        <div className="adp-active-filter-list">
          {activeFilterPills.map((pill) => (
            <span key={pill} className="adp-active-filter-pill">
              {pill}
            </span>
          ))}
        </div>
      </section>

      <section className="adp-composition-card">
        <div className="adp-composition-header">
          <div>
            <span className="adp-section-kicker">Corpus health</span>
            <h2>Dataset quality and crawl shape</h2>
          </div>
          <small>
            These counts reflect the whole stored Sleeper corpus, not just the current board filter.
          </small>
        </div>

        <SummaryGrid cards={corpusHealthCards} />

        <DistributionGrid
          groups={reportDistributionGroups}
          emptyLabel="No tracked rows"
          rowLimit={8}
        />
      </section>

      <section className="adp-composition-card">
        <div className="adp-composition-header">
          <div>
            <span className="adp-section-kicker">Composition</span>
            <h2>Current sample makeup</h2>
          </div>
          <small>
            Counts reflect the discovered corpus available around this filter slice.
          </small>
        </div>

        <DistributionGrid
          groups={sampleCompositionGroups}
          emptyLabel="No matching sample"
        />
      </section>
    </>
  );
}
