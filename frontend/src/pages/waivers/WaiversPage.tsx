import { useState } from 'react';

import './WaiversPage.css';

import { useValuePreference } from '@/context/useValuePreference';
import { AvailablePlayersTab } from './AvailablePlayersTab';
import { WaiversOverviewTab } from './WaiversOverviewTab';
import { WaiversTabs } from './WaiversTabs';
import { BulkClaimsTab } from './BulkClaimsTab';


export const WaiversPage = () => {
  const valuePreference = useValuePreference();
  const [activeTab, setActiveTab] = useState<
    'overview'
    | 'available'
    | 'bulk'
  >('overview');
  const valueBasis = valuePreference.preference;

  return (
    <div className="waivers-page">
      <section className="waivers-page-header">
        <div>
          <p className="waivers-eyebrow">
            WAIVER ASSISTANT
          </p>

          <h1>
            Find the strongest waiver moves
          </h1>

          <p className="waivers-page-description">
            Compare available players and submit
            waiver claims across your leagues.
          </p>
        </div>

      </section>

      <WaiversTabs
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      {
        activeTab === 'overview'
          ? (
            <WaiversOverviewTab
              valueBasis={valueBasis}
            />
          )
          : activeTab === 'available'
            ? (
              <AvailablePlayersTab
                valueBasis={valueBasis}
              />
            )
            : (
              <BulkClaimsTab
                valueBasis={valueBasis}
              />
            )
      }
    </div>
  );
};
