import type { DashboardSummary as DashboardSummaryType } from '@/types';
interface Props {
  summary: DashboardSummaryType;
}

const summaryItems = [
  {
    label: 'Leagues',
    value: (summary: DashboardSummaryType) =>
      summary.league_count.toLocaleString(),
  },
  {
    label: 'Players',
    value: (summary: DashboardSummaryType) =>
      summary.player_count.toLocaleString(),
  },
  {
    label: 'Total KTC',
    value: (summary: DashboardSummaryType) =>
      summary.total_ktc_value.toLocaleString(),
  },
  {
    label: 'Total FC',
    value: (summary: DashboardSummaryType) =>
      summary.total_fc_value.toLocaleString(),
  },
  {
    label: 'Dynasty starter WAR',
    value: (summary: DashboardSummaryType) =>
      summary.total_dynasty_starter_war.toFixed(2),
  },
  {
    label: 'Dynasty roster WAR',
    value: (summary: DashboardSummaryType) =>
      summary.total_dynasty_roster_war.toFixed(2),
  },
  {
    label: 'Redraft starter WAR',
    value: (summary: DashboardSummaryType) =>
      summary.total_redraft_starter_war.toFixed(2),
  },
  {
    label: 'Redraft roster WAR',
    value: (summary: DashboardSummaryType) =>
      summary.total_redraft_roster_war.toFixed(2),
  },
  {
    label: 'Average age',
    value: (summary: DashboardSummaryType) =>
      summary.average_age.toFixed(1),
  },
] as const;

export function DashboardSummary({
  summary,
}: Props) {
  return (
    <section className="dashboard-section">
      <div className="dashboard-section-header">
        <div>
          <p className="dashboard-section-kicker">
            Snapshot
          </p>

          <h2 className="dashboard-section-title">
            Portfolio totals
          </h2>
        </div>
      </div>

      <div className="summary-grid">
        {summaryItems.map((item) => (
          <div
            key={item.label}
            className="summary-card"
          >
            <span className="summary-card-label">
              {item.label}
            </span>

            <strong className="summary-card-value">
              {item.value(summary)}
            </strong>
          </div>
        ))}
      </div>
    </section>
  );
}
