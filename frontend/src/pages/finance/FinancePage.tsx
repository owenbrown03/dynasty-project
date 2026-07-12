import { useEffect, useState } from 'react';

import { LoadingState } from '@/components/feedback/LoadingState';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';
import {
  useFinanceSummary,
  useSaveFinanceSeason,
} from '@/hooks/sleeper/useUsers';
import type {
  FinanceLeagueSeasonEntry,
} from '@/types';
import { notify } from '@/utils/notify';
import { formatNumber } from '@/utils/format';

import './FinancePage.css';


function formatCurrency(
  value: number,
) {
  return new Intl.NumberFormat(
    'en-US',
    {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    },
  ).format(value);
}


function FinanceSeasonCard({
  entry,
  onSave,
  saving,
}: {
  entry: FinanceLeagueSeasonEntry;
  onSave: (
    entry: FinanceLeagueSeasonEntry,
    buyInAmount: number,
    winningsAmount: number,
  ) => Promise<void>;
  saving: boolean;
}) {
  const [buyInAmount, setBuyInAmount] = useState(
    entry.buy_in_amount.toString(),
  );
  const [winningsAmount, setWinningsAmount] = useState(
    entry.winnings_amount.toString(),
  );

  useEffect(() => {
    setBuyInAmount(
      entry.buy_in_amount.toString(),
    );
    setWinningsAmount(
      entry.winnings_amount.toString(),
    );
  }, [entry]);

  return (
    <article className="finance-card">
      <header className="finance-card-header">
        <div>
          <p className="finance-card-kicker">
            {entry.season}
          </p>
          <h2 className="finance-card-title">
            {entry.league_name}
          </h2>
          <p className="finance-card-subtitle">
            {
              entry.rank !== null
                ? `Rank ${entry.rank} of ${entry.total_rosters}`
                : `${entry.total_rosters} teams`
            }
            {
              entry.points_for !== null
                ? ` · PF ${formatNumber(entry.points_for)}`
                : ''
            }
          </p>
        </div>

        <div className="finance-card-net">
          <span>Net</span>
          <strong>{formatCurrency(entry.net_amount)}</strong>
        </div>
      </header>

      <div className="finance-card-grid">
        <div>
          <span>Buy-in</span>
          <strong>{formatCurrency(entry.buy_in_amount)}</strong>
        </div>
        <div>
          <span>Winnings</span>
          <strong>{formatCurrency(entry.winnings_amount)}</strong>
        </div>
        <div>
          <span>Projected current payout</span>
          <strong>{formatCurrency(entry.projected_winnings_amount)}</strong>
        </div>
      </div>

      <div className="finance-form-grid">
        <label>
          <span>Buy-in amount</span>
          <input
            type="number"
            min="0"
            step="1"
            value={buyInAmount}
            onChange={(event) => {
              setBuyInAmount(event.target.value);
            }}
          />
        </label>

        <label>
          <span>Winnings</span>
          <input
            type="number"
            min="0"
            step="1"
            value={winningsAmount}
            onChange={(event) => {
              setWinningsAmount(event.target.value);
            }}
          />
        </label>

        <button
          type="button"
          className="button-secondary"
          disabled={saving}
          onClick={() => {
            void onSave(
              entry,
              Number(buyInAmount) || 0,
              Number(winningsAmount) || 0,
            );
          }}
        >
          {saving ? 'Saving...' : 'Save'}
        </button>
      </div>
    </article>
  );
}


export function FinancePage() {
  const connection = useSleeperConnection();
  const finance = useFinanceSummary(
    connection.linked,
  );
  const saveFinanceMutation = useSaveFinanceSeason();

  const handleSave = async (
    entry: FinanceLeagueSeasonEntry,
    buyInAmount: number,
    winningsAmount: number,
  ) => {
    try {
      await saveFinanceMutation.mutateAsync({
        league_id: entry.league_id,
        season: entry.season,
        buy_in_amount: buyInAmount,
        winnings_amount: winningsAmount,
      });
      notify.success('Finance entry saved.');
    } catch {
      notify.error('Unable to save finance entry.');
    }
  };

  return (
    <main className="finance-page">
      <section className="finance-page-header">
        <div>
          <p className="page-eyebrow">Finance</p>
          <h1 className="finance-page-title">
            League finance tracker
          </h1>
          <p className="finance-page-description">
            Track buy-ins, winnings, net results, and a simple in-season payout
            projection for your linked Sleeper leagues.
          </p>
        </div>
      </section>

      {
        !connection.linked
          ? (
            <div className="finance-empty-state">
              Link a Sleeper account to use the finance tracker.
            </div>
          )
          : null
      }

      {
        connection.linked && finance.loading
          ? (
            <LoadingState
              label="Loading finance tracker..."
              className="finance-empty-state"
            />
          )
          : null
      }

      {
        connection.linked && !finance.loading && finance.error
          ? (
            <div className="finance-empty-state">
              Unable to load finance data.
            </div>
          )
          : null
      }

      {
        finance.data
          ? (
            <>
              <section className="finance-summary-grid">
                <article className="finance-summary-card">
                  <span>Total buy-ins</span>
                  <strong>{formatCurrency(finance.data.total_buy_ins)}</strong>
                </article>

                <article className="finance-summary-card">
                  <span>Total winnings</span>
                  <strong>{formatCurrency(finance.data.total_winnings)}</strong>
                </article>

                <article className="finance-summary-card">
                  <span>Total net</span>
                  <strong>{formatCurrency(finance.data.total_net)}</strong>
                </article>

                <article className="finance-summary-card">
                  <span>Projected current payouts</span>
                  <strong>{formatCurrency(finance.data.projected_current_winnings)}</strong>
                </article>
              </section>

              <section className="finance-card-grid">
                {
                  finance.data.seasons.map((entry) => (
                    <FinanceSeasonCard
                      key={`${entry.league_id}-${entry.season}`}
                      entry={entry}
                      onSave={handleSave}
                      saving={saveFinanceMutation.isPending}
                    />
                  ))
                }
              </section>
            </>
          )
          : null
      }
    </main>
  );
}
