import {
  useState,
} from 'react';

import { BulkOffersTab } from './BulkOffersTab';
import { TradeResearchTab } from './TradeResearchTab';

import './TradesPage.css';


type TradesTab = 'bulk-offers' | 'research';


export const TradesPage = () => {
  const [activeTab, setActiveTab] = useState<TradesTab>(
    'bulk-offers',
  );

  return (
    <main className="trades-page">
      <div className="trades-tabs">
        <button
          className={
            activeTab === 'bulk-offers'
              ? 'active'
              : ''
          }
          onClick={() => {
            setActiveTab('bulk-offers');
          }}
        >
          Bulk Offers
        </button>

        <button
          className={
            activeTab === 'research'
              ? 'active'
              : ''
          }
          onClick={() => {
            setActiveTab('research');
          }}
        >
          Trade Research
        </button>
      </div>

      {
        activeTab === 'bulk-offers'
          ? <BulkOffersTab />
          : <TradeResearchTab />
      }
    </main>
  );
};