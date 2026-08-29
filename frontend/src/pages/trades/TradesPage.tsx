import {
  useEffect,
  useState,
} from 'react';
import { useLocation } from 'react-router';

import { BulkOffersTab } from './BulkOffersTab';
import {
  TradeCalculatorTab,
  type TradeCalculatorBulkOfferSeed,
} from './TradeCalculatorTab';
import { TradeSignalsTab } from './TradeSignalsTab';

import './TradesPage.css';


type TradesTab =
  | 'bulk-offers'
  | 'calculator'
  | 'signals';


export const TradesPage = () => {
  const location = useLocation();
  const locationSeed = (location.state as { seed?: TradeCalculatorBulkOfferSeed } | null)?.seed ?? null;
  const [activeTab, setActiveTab] = useState<TradesTab>(
    'bulk-offers',
  );
  const [bulkOfferSeed, setBulkOfferSeed] = useState<TradeCalculatorBulkOfferSeed | null>(
    locationSeed,
  );

  useEffect(() => {
    const nextSeed = (location.state as { seed?: TradeCalculatorBulkOfferSeed } | null)?.seed;
    if (nextSeed) {
      setBulkOfferSeed(nextSeed);
      setActiveTab('bulk-offers');
    }
  }, [location.state]);

  return (
    <main className="trades-page">
      <section className="page-header">
        <div>
          <p className="page-eyebrow">Trades</p>
          <h1 className="page-title">Trade tools</h1>
          <p className="page-description">
            Research completed deals and build repeatable cross-league offers
            without leaving the dashboard.
          </p>
        </div>
      </section>

      <div className="trades-tabs" role="tablist" aria-label="Trade tools">
        <button
          className={
            activeTab === 'bulk-offers'
              ? 'trades-tab-button active'
              : 'trades-tab-button'
          }
          onClick={() => {
            setActiveTab('bulk-offers');
          }}
          type="button"
        >
          Bulk Offers
        </button>

        <button
          className={
            activeTab === 'calculator'
              ? 'trades-tab-button active'
              : 'trades-tab-button'
          }
          onClick={() => {
            setActiveTab('calculator');
          }}
          type="button"
        >
          Calculator
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
        activeTab === 'bulk-offers'
          ? <BulkOffersTab seed={bulkOfferSeed} />
          : activeTab === 'calculator'
            ? (
              <TradeCalculatorTab
                onSendToBulkOffers={(seed) => {
                  setBulkOfferSeed(seed);
                  setActiveTab('bulk-offers');
                }}
              />
            )
            : <TradeSignalsTab />
      }
    </main>
  );
};
