import './TradeCard.css';
import type { Transaction } from '../../types';
import { UserCard } from './UserCard';

interface Props {
  tx: Transaction;
}

export function TradeCard({ tx }: Props) {
  return (
    <div className="trade-card">
      <header className="trade-header">
        <div className="trade-header-main">
          <span className="trade-header-kicker">League</span>
          <span className="league-name">{tx.league_name}</span>
          {tx.league_settings.length > 0 ? (
            <div className="trade-league-settings" aria-label="League settings">
              {tx.league_settings.map((setting) => (
                <span
                  key={`${tx.transaction_id}-${setting}`}
                  className="trade-league-setting"
                >
                  {setting}
                </span>
              ))}
            </div>
          ) : null}
        </div>

        <span className="trade-time">
          {new Date(tx.time_ms).toLocaleString()}
        </span>
      </header>

      <div className="trade-users-row">
        {tx.users.map((user, index) => (
          <UserCard
            key={`${tx.transaction_id}-${index}`}
            user={user}
          />
        ))}
      </div>
    </div>
  );
}
