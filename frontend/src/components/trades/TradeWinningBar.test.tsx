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
        teamAName="Side A"
        teamBName="Side B"
        teamANet={8000}
        teamBNet={4000}
      />
    );

    expect(screen.getByText(/Favors Side A/i)).toBeInTheDocument();
    expect(screen.getByText(/Add a player or pick worth/i)).toBeInTheDocument();
    expect(screen.getByText(/to Side B to even trade/i)).toBeInTheDocument();
  });

  it('renders Favors Team 2 when Team 2 has higher value', () => {
    render(
      <TradeWinningBar
        teamAName="Squad 1"
        teamBName="Squad 2"
        teamANet={3000}
        teamBNet={7500}
      />
    );

    expect(screen.getByText(/Favors Squad 2/i)).toBeInTheDocument();
    expect(screen.getByText(/to Squad 1 to even trade/i)).toBeInTheDocument();
  });

  it('renders WAR formatting when valueBasis is dynasty_starter_war', () => {
    render(
      <TradeWinningBar
        teamAName="Club 1"
        teamBName="Club 2"
        teamANet={8.5}
        teamBNet={4.2}
        valueBasis="dynasty_starter_war"
      />
    );

    expect(screen.getByText(/Favors Club 1/i)).toBeInTheDocument();
    expect(screen.getByText(/4.30 WAR/i)).toBeInTheDocument();
  });

  it('renders empty state instructions when no assets are provided', () => {
    render(
      <TradeWinningBar
        teamAName="Alpha"
        teamBName="Beta"
        teamANet={0}
        teamBNet={0}
      />
    );

    expect(screen.getByText(/Add players or picks to both sides/i)).toBeInTheDocument();
  });
});
