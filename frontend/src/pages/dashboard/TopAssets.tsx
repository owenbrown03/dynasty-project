import type { DashboardAsset } from '@/types';
import { formatNumber } from '@/utils/format';

interface Props {
  assets: DashboardAsset[];
}

export function TopAssets({
  assets,
}: Props) {
  return (
    <section className="dashboard-section">
      <div className="dashboard-section-header">
        <div>
          <p className="dashboard-section-kicker">
            Assets
          </p>

          <h2 className="dashboard-section-title">
            Top rostered pieces
          </h2>
        </div>
      </div>

      <div className="top-assets-list">
        {assets.map((player, index) => (
          <div
            key={player.player_id}
            className="top-asset-row"
          >
            <div className="top-asset-rank">
              {index + 1}
            </div>

            <div className="top-asset-main">
              <strong className="top-asset-name">
                {player.name}
              </strong>

              <span className="top-asset-meta">
                {player.position}
                {' '}
                {player.team ?? 'FA'}
              </span>
            </div>

            <div className="top-asset-stats">
              <span>
                KTC {formatNumber(player.ktc_value)}
              </span>

              <span>
                FC {formatNumber(player.fc_value)}
              </span>

              <span>
                WAR {(player.roster_war ?? 0).toFixed(2)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
