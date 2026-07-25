import {
  formatMetric,
} from './myValues.utils';

interface MyValuesMetricCardProps {
  label: string;
  market: number | null | undefined;
  mine: number | null | undefined;
  delta: number | null | undefined;
}

export function MyValuesMetricCard({
  label,
  market,
  mine,
  delta,
}: MyValuesMetricCardProps) {
  const deltaClassName = (
    delta == null
      ? ''
      : delta > 0
        ? 'positive'
        : delta < 0
          ? 'negative'
          : 'neutral'
  );

  return (
    <div className="my-values-metric-card">
      <span>{label}</span>
      <strong>{formatMetric(mine)}</strong>
      <div className="my-values-metric-meta">
        <p>Market {formatMetric(market)}</p>
        <p className={deltaClassName}>
          Delta {delta == null ? '--' : `${delta > 0 ? '+' : ''}${formatMetric(delta)}`}
        </p>
      </div>
    </div>
  );
}
