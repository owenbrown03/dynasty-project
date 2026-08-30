import {
  useEffect,
  useState,
} from 'react';
import { useLocation } from 'react-router';

import { TradeBuilderTab } from './BulkOffersTab';
import { TradeSignalsTab } from './TradeSignalsTab';
import type { TradeCalculatorBulkOfferSeed } from './TradeCalculatorTab';

import './TradesPage.css';


type TradesTab =
  | 'trade-builder'
  | 'signals';


export const TradesPage = () => {
  const location = useLocation();
  const locationSeed = (location.state as { seed?: TradeCalculatorBulkOfferSeed } | null)?.seed ?? null;
  const [activeTab, setActiveTab] = useState<TradesTab>(
    'trade-builder',
  );
  const [bulkOfferSeed, setBulkOfferSeed] = useState<TradeCalculatorBulkOfferSeed | null>(
    locationSeed,
  );

  useEffect(() => {
    const nextSeed = (location.state as { seed?: TradeCalculatorBulkOfferSeed } | null)?.seed;
    if (nextSeed) {
      setBulkOfferSeed(nextSeed);
      setActiveTab('trade-builder');
    }
  }, [location.state]);

  return (
    <main className="trades-page">
      <section className="page-header">
        <div>
          <p className="page-eyebrow">Trades</p>
          <h1 className="page-title">Trade Builder</h1>
          <p className="page-description">
            Evaluate player and pick values, calculate deal balance, and dispatch
            cross-league trade offers across all your rosters.
          </p>
        </div>
      </section>

      <div className="trades-tabs" role="tablist" aria-label="Trade tools">
        <button
          className={
            activeTab === 'trade-builder'
              ? 'trades-tab-button active'
              : 'trades-tab-button'
          }
          onClick={() => {
            setActiveTab('trade-builder');
          }}
          type="button"
        >
          Trade Builder
        </button>

        <button
          className={
            activeTab === 'signals'
              ? 'trades-tab-button active'
              : 'trades-tab-button'
          }
          onClick={() => {
            setActiveTab('signals');
          }}
          type="button"
        >
          Trade Signals
        </button>
      </div>

      {
        activeTab === 'trade-builder'
          ? <TradeBuilderTab seed={bulkOfferSeed} />
          : <TradeSignalsTab />
      }
    </main>
  );
};
