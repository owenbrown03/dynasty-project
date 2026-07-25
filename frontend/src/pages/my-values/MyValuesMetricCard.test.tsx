import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { MyValuesMetricCard } from './MyValuesMetricCard';

describe('MyValuesMetricCard', () => {
  it('renders market, custom, and signed positive delta values', () => {
    render(
      <MyValuesMetricCard
        label="Dynasty roster WAR"
        market={4.25}
        mine={5.5}
        delta={1.25}
      />,
    );

    expect(screen.getByText('Dynasty roster WAR')).toBeInTheDocument();
    expect(screen.getByText('5.50')).toBeInTheDocument();
    expect(screen.getByText('Market 4.25')).toBeInTheDocument();
    expect(screen.getByText('Delta +1.25')).toHaveClass('positive');
  });

  it('renders missing deltas without a sign class', () => {
    render(
      <MyValuesMetricCard
        label="Redraft starter WAR"
        market={null}
        mine={null}
        delta={null}
      />,
    );

    expect(screen.getByText('Market --')).toBeInTheDocument();
    expect(screen.getByText('Delta --')).not.toHaveClass('positive');
  });
});
