import { Skeleton } from '@/components/feedback/Skeleton';
import './LeagueCard.css';
import './RosterCard.css';
import './PlayerTable.css';
import './LeagueDashboard.css';

interface LeagueDetailsSkeletonProps {
  activeTab?: 'overview' | 'charts' | 'analytics' | 'advisor';
}

export function LeagueDetailsSkeleton({
  activeTab = 'overview',
}: LeagueDetailsSkeletonProps) {
  if (activeTab === 'charts') {
    return (
      <div className="league-card" style={{ gap: '16px', padding: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Skeleton variant="text" width={100} height={12} />
            <div style={{ marginTop: 4 }}>
              <Skeleton variant="title" width={200} height={22} />
            </div>
          </div>
          <Skeleton variant="block" width={160} height={32} radius={6} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: 12 }}>
          {[92, 85, 78, 74, 68, 62, 58, 52, 48, 42, 35, 28].map((pct, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Skeleton variant="text" width={120} height={16} />
              <div style={{ flex: 1 }}>
                <Skeleton variant="block" width={`${pct}%`} height={24} radius={4} />
              </div>
              <Skeleton variant="text" width={48} height={16} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (activeTab === 'analytics') {
    return (
      <div className="league-card" style={{ gap: '16px', padding: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Skeleton variant="text" width={100} height={12} />
            <div style={{ marginTop: 4 }}>
              <Skeleton variant="title" width={220} height={22} />
            </div>
          </div>
          <Skeleton variant="block" width={140} height={32} radius={6} />
        </div>
        <div style={{ height: '320px', display: 'flex', alignItems: 'flex-end', gap: '14px', paddingTop: 30 }}>
          {[40, 65, 80, 55, 90, 70, 85, 60, 75, 50, 65, 95].map((height, idx) => (
            <div key={idx} style={{ flex: 1, height: '100%', display: 'flex', alignItems: 'flex-end' }}>
              <Skeleton variant="block" width="100%" height={`${height}%`} radius={4} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="league-card" aria-label="Loading league details...">
      {/* League Header */}
      <header className="league-header">
        <div className="league-header-identity">
          <Skeleton variant="circle" width={42} height={42} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <Skeleton variant="text" width={60} height={10} />
            <Skeleton variant="title" width={240} height={20} />
            <Skeleton variant="text" width={320} height={12} />
          </div>
        </div>
      </header>

      {/* League Overview / Settings Grid */}
      <section className="league-settings-panel league-overview-panel">
        <div className="league-settings-header">
          <Skeleton variant="text" width={100} height={12} />
        </div>
        <div className="league-overview-content">
          <div className="league-settings-grid">
            {Array.from({ length: 6 }).map((_, idx) => (
              <div key={idx} className="league-settings-item">
                <Skeleton variant="text" width={60} height={10} />
                <div style={{ marginTop: 2 }}>
                  <Skeleton variant="text" width={80} height={16} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Roster Cards Grid */}
      <div className="rosters">
        {Array.from({ length: 3 }).map((_, rosterIdx) => (
          <div key={rosterIdx} className="roster-card">
            {/* Roster Header */}
            <div className="roster-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <Skeleton variant="circle" width={36} height={36} />
                <div className="roster-header-main">
                  <Skeleton variant="text" width={40} height={10} />
                  <Skeleton variant="title" width={160} height={16} />
                  <Skeleton variant="text" width={100} height={12} />
                </div>
              </div>
              <div className="roster-summary-hero">
                <Skeleton variant="text" width={50} height={10} />
                <Skeleton variant="title" width={70} height={18} />
              </div>
            </div>

            {/* Summary Stat Grid */}
            <div className="roster-summary-grid">
              {Array.from({ length: 4 }).map((_, statIdx) => (
                <div key={statIdx} className="roster-summary-stat">
                  <Skeleton variant="text" width={50} height={10} />
                  <div style={{ marginTop: 2 }}>
                    <Skeleton variant="text" width={60} height={14} />
                  </div>
                </div>
              ))}
            </div>

            {/* Player Table Skeleton */}
            <div className="player-table-wrap">
              <table className="player-table">
                <thead>
                  <tr>
                    <th className="player-table-slot-col"><Skeleton variant="text" width={30} height={12} /></th>
                    <th><Skeleton variant="text" width={80} height={12} /></th>
                    <th className="player-table-position-col"><Skeleton variant="text" width={30} height={12} /></th>
                    <th className="player-table-team-col"><Skeleton variant="text" width={35} height={12} /></th>
                    <th className="player-table-num-col"><Skeleton variant="text" width={35} height={12} /></th>
                    <th className="player-table-ud-col"><Skeleton variant="text" width={25} height={12} /></th>
                    <th className="player-table-num-col"><Skeleton variant="text" width={45} height={12} /></th>
                  </tr>
                </thead>
                <tbody>
                  {Array.from({ length: 5 }).map((_, playerIdx) => (
                    <tr key={playerIdx}>
                      <td className="player-table-slot-cell">
                        <Skeleton variant="block" width={36} height={18} radius={4} />
                      </td>
                      <td className="player-table-name-cell">
                        <div className="player-with-avatar">
                          <Skeleton variant="circle" width={24} height={24} />
                          <Skeleton variant="text" width={110} height={14} />
                        </div>
                      </td>
                      <td className="player-table-position-cell">
                        <Skeleton variant="text" width={24} height={12} />
                      </td>
                      <td className="player-table-team-cell">
                        <Skeleton variant="text" width={28} height={12} />
                      </td>
                      <td className="player-table-num-cell">
                        <Skeleton variant="text" width={32} height={12} />
                      </td>
                      <td className="player-table-ud-cell">
                        <Skeleton variant="text" width={28} height={12} />
                      </td>
                      <td className="player-table-num-cell">
                        <Skeleton variant="text" width={40} height={12} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
