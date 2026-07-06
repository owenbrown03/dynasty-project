import { useState } from 'react';

import './WaiversPage.css';

import type { ValueBasis } from '@/types';

import { AvailablePlayersTab } from './AvailablePlayersTab';
import { ValueBasisSelector } from './ValueBasisSelector';
import { WaiversOverviewTab } from './WaiversOverviewTab';
import { WaiversTabs } from './WaiversTabs';
import { BulkClaimsTab } from './BulkClaimsTab';


export const WaiversPage = () => {
  const [activeTab, setActiveTab] = useState<
    'overview'
    | 'available'
    | 'bulk'
  >('overview');

  const [valueBasis, setValueBasis] = useState<ValueBasis>(
    'ktc',
  );

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

        <ValueBasisSelector
          valueBasis={valueBasis}
          onChange={setValueBasis}
        />
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