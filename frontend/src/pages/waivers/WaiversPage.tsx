import { useMemo } from 'react';
import { useSearchParams } from 'react-router';

import './WaiversPage.css';

import { useValuePreference } from '@/context/useValuePreference';
import { AvailablePlayersTab } from './AvailablePlayersTab';
import { RecentlyDroppedTab } from './RecentlyDroppedTab';
import { WaiversOverviewTab } from './WaiversOverviewTab';
import { WaiversTabs } from './WaiversTabs';
import { BulkClaimsTab } from './BulkClaimsTab';


export const WaiversPage = () => {
  const valuePreference = useValuePreference();
  const valueBasis = valuePreference.preference;
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = useMemo(() => {
    const tab = searchParams.get('tab');

    if (
      tab === 'overview'
      || tab === 'available'
      || tab === 'recent-drops'
      || tab === 'bulk'
    ) {
      return tab;
    }

    return 'overview';
  }, [searchParams]);
  const selectedLeagueId = (
    searchParams.get('league_id')
    ?? undefined
  );

  const setActiveTab = (
    nextTab: (
      'overview'
      | 'recent-drops'
      | 'available'
      | 'bulk'
    ),
  ) => {
    const next = new URLSearchParams(searchParams);
    next.set('tab', nextTab);
    setSearchParams(next);
  };

  const setSelectedLeagueId = (
    nextLeagueId: string | undefined,
  ) => {
    const next = new URLSearchParams(searchParams);
    next.set('tab', 'available');

    if (nextLeagueId) {
      next.set('league_id', nextLeagueId);
    } else {
      next.delete('league_id');
    }

    setSearchParams(next);
  };

  return (
    <div className="waivers-page">
      <section className="page-header">
        <div>
          <p className="page-eyebrow">
            WAIVER ASSISTANT
          </p>

          <h1 className="page-title">
            Find the strongest waiver moves
          </h1>

          <p className="page-description">
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
              onOpenAvailableLeague={
                setSelectedLeagueId
              }
            />
          )
          : activeTab === 'recent-drops'
            ? (
              <RecentlyDroppedTab
                valueBasis={valueBasis}
              />
            )
            : activeTab === 'available'
            ? (
              <AvailablePlayersTab
                valueBasis={valueBasis}
                selectedLeagueId={
                  selectedLeagueId
                }
                onSelectedLeagueIdChange={
                  setSelectedLeagueId
                }
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
