import {
  useState,
} from 'react';

import { BulkOffersTab } from './BulkOffersTab';
import {
  TradeCalculatorTab,
  type TradeCalculatorBulkOfferSeed,
} from './TradeCalculatorTab';
import { TradeResearchTab } from './TradeResearchTab';

import './TradesPage.css';


type TradesTab =
  | 'bulk-offers'
  | 'calculator'
  | 'research';


export const TradesPage = () => {
  const [activeTab, setActiveTab] = useState<TradesTab>(
    'bulk-offers',
  );
  const [bulkOfferSeed, setBulkOfferSeed] = useState<TradeCalculatorBulkOfferSeed | null>(
    null,
  );

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
            activeTab === 'research'
              ? 'trades-tab-button active'
              : 'trades-tab-button'
          }
          onClick={() => {
            setActiveTab('research');
          }}
          type="button"
        >
          Trade Research
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
            : <TradeResearchTab />
      }
    </main>
  );
};
