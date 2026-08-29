import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { TradeWinningBar } from './TradeWinningBar';

describe('TradeWinningBar', () => {
  it('renders even trade when values are balanced', () => {
    render(
      <TradeWinningBar
        teamAName="Team 1"
        teamBName="Team 2"
        teamANet={5000}
        teamBNet={5000}
      />
    );

    expect(screen.getByText(/Even Trade/i)).toBeInTheDocument();
    expect(screen.getByText(/Values are balanced/i)).toBeInTheDocument();
  });

  it('renders Favors Team 1 when Team 1 has higher value', () => {
    render(
      <TradeWinningBar
        teamAName="Team 1"
        teamBName="Team 2"
        teamANet={8000}
        teamBNet={4000}
      />
    );

    expect(screen.getByText(/Favors Team 1/i)).toBeInTheDocument();
    expect(screen.getByText(/Add a player or pick worth/i)).toBeInTheDocument();
    expect(screen.getByText(/to Team 2 to even trade/i)).toBeInTheDocument();
  });

  it('renders Favors Team 2 when Team 2 has higher value', () => {
    render(
      <TradeWinningBar
        teamAName="Team 1"
        teamBName="Team 2"
        teamANet={3000}
        teamBNet={7500}
      />
    );

    expect(screen.getByText(/Favors Team 2/i)).toBeInTheDocument();
    expect(screen.getByText(/to Team 1 to even trade/i)).toBeInTheDocument();
  });

  it('renders empty state instructions when no assets are provided', () => {
    render(
      <TradeWinningBar
        teamAName="Team 1"
        teamBName="Team 2"
        teamANet={0}
        teamBNet={0}
      />
    );

    expect(screen.getByText(/Add players or picks to both sides/i)).toBeInTheDocument();
  });
});
