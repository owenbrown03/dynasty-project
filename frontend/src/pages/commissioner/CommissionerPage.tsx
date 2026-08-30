import {
  useEffect,
  useMemo,
  useState,
} from 'react';
import {
  useNavigate,
  useParams,
  useSearchParams,
} from 'react-router';

import { Skeleton } from '@/components/feedback/Skeleton';
import { useAuth } from '@/hooks/useAuth';
import { useValuePreference } from '@/context/useValuePreference';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';
import {
  useCommissionerOrphans,
  useCommissionerWorkspace,
  useSaveCommissionerDues,
  useSaveCommissionerSettings,
  useSaveCommissionerNote,
} from '@/hooks/sleeper/useUsers';
import { notify } from '@/utils/notify';
import type {
  CommissionerLeagueDuesEntry,
  CommissionerWorkspaceLeague,
  ValueBasis,
} from '@/types';
import {
  VALUE_BASIS_OPTIONS,
  getValueBasisOptions,
} from '@/pages/waivers/waiver.constants';
import { CommissionerOrphanCard } from './CommissionerOrphanCard';
import { CommissionerCutdownsTab } from './CommissionerCutdownsTab';

import './CommissionerPage.css';


type CommissionerTab =
  | 'orphans'
  | 'workspace'
  | 'cutdowns';


function isValueBasis(
  value: string | null,
): value is ValueBasis {
  return VALUE_BASIS_OPTIONS.some(
    (option) => option.value === value,
  );
}

function CommissionerCardSkeleton({
  mode,
}: {
  mode: 'orphans' | 'workspace'
  | 'cutdowns';
}) {
  return (
    <article className="commissioner-card">
      <header className="commissioner-card-header">
        <div className="commissioner-card-heading">
          <Skeleton width={58} variant="text" />
          <Skeleton width="72%" variant="title" />
          <Skeleton width={96} variant="text" />
        </div>

        <div className="commissioner-card-stats commissioner-card-stats-skeleton">
          {
            Array.from({ length: 3 }).map((_, index) => (
              <div key={index}>
                <Skeleton width={84} variant="text" />
                <Skeleton width={72} height={22} />
              </div>
            ))
          }
        </div>
      </header>

      {
        mode === 'orphans'
          ? (
            <>
              <div className="commissioner-badge-row">
                {
                  Array.from({ length: 5 }).map((_, index) => (
                    <Skeleton width={72} height={34} key={index} />
                  ))
                }
              </div>

              <section className="commissioner-section">
                <div className="commissioner-section-header">
                  <Skeleton width={150} variant="text" />
                </div>
                <div className="commissioner-list">
                  {
                    Array.from({ length: 4 }).map((_, index) => (
                      <div className="commissioner-player-row" key={index}>
                        <div className="player-with-avatar">
                          <Skeleton width={34} height={34} radius={4} />
                          <div className="player-with-avatar-copy">
                            <Skeleton width={150} variant="title" />
                            <Skeleton width={80} variant="text" />
                          </div>
                        </div>
                        <Skeleton width={52} height={18} />
                      </div>
                    ))
                  }
                </div>
              </section>
            </>
          )
          : (
            <>
              <section className="commissioner-section">
                <div className="commissioner-section-header">
                  <Skeleton width={160} variant="text" />
                </div>
                <div className="commissioner-due-settings">
                  <Skeleton height={46} />
                  <Skeleton width={160} height={42} />
                </div>
              </section>

              <section className="commissioner-section">
                <div className="commissioner-section-header">
                  <Skeleton width={120} variant="text" />
                </div>
                <div className="commissioner-list">
                  {
                    Array.from({ length: 3 }).map((_, index) => (
                      <div className="commissioner-due-row" key={index}>
                        <div className="commissioner-due-copy">
                          <Skeleton width={140} variant="title" />
                          <Skeleton width="70%" variant="text" />
                        </div>
                        <Skeleton width={100} height={36} />
                      </div>
                    ))
                  }
                </div>
              </section>
            </>
          )
      }
    </article>
  );
}

function CommissionerCardGridSkeleton({
  mode,
}: {
  mode: 'orphans' | 'workspace'
  | 'cutdowns';
}) {
  return (
    <section
      className="commissioner-card-grid"
      role="status"
      aria-live="polite"
    >
      <span className="skeleton-sr-label">
        {
          mode === 'orphans'
            ? 'Loading commissioner view...'
            : 'Loading league dues tracker...'
        }
      </span>
      {
        Array.from({ length: 4 }).map((_, index) => (
          <CommissionerCardSkeleton
            key={index}
            mode={mode}
          />
        ))
      }
    </section>
  );
}


function CommissionerWorkspaceCard({
  league,
  onSaveNote,
  onSaveDues,
  onSaveSettings,
  savingNote,
  savingDues,
  savingDuesMap,
  savingSettings,
}: {
  league: CommissionerWorkspaceLeague;
  onSaveNote: (
    leagueId: string,
    note: string,
  ) => Promise<void>;
  onSaveDues: (
    entry: CommissionerLeagueDuesEntry,
    buyInAmount: number | null,
    isPaid: boolean,
  ) => Promise<void>;
  onSaveSettings: (
    leagueId: string,
    paidYearsAhead: number,
  ) => Promise<void>;
  savingNote: boolean;
  savingDues: boolean;
  savingDuesMap?: Record<string, boolean>;
  savingSettings: boolean;
}) {
  const [note, setNote] = useState(league.note);
  const [paidYearsAhead, setPaidYearsAhead] = useState(
    league.paid_years_ahead.toString(),
  );
  const [duesDrafts, setDuesDrafts] = useState<
    Record<string, { amount: string; isPaid: boolean }>
  >(() => Object.fromEntries(
    league.dues.map((entry) => [
      `${entry.roster_id}-${entry.season}`,
      {
        amount: entry.buy_in_amount?.toString() ?? '',
        isPaid: entry.is_paid,
      },
    ]),
  ));

  useEffect(() => {
    setNote(league.note);
    setPaidYearsAhead(
      league.paid_years_ahead.toString(),
    );
    setDuesDrafts(
      Object.fromEntries(
        league.dues.map((entry) => [
          `${entry.roster_id}-${entry.season}`,
          {
            amount: entry.buy_in_amount?.toString() ?? '',
            isPaid: entry.is_paid,
          },
        ]),
      ),
    );
  }, [league]);

  return (
    <article className="commissioner-card">
      <header className="commissioner-card-header">
        <div>
          <p className="commissioner-card-kicker">
            League Dues Tracker
          </p>
          <h2 className="commissioner-card-title">
            {league.league_name}
          </h2>
          <p className="commissioner-card-subtitle">
            {league.league_season} season
          </p>
        </div>
      </header>

      <section className="commissioner-section">
        <div className="commissioner-section-header">
          <p>Dues settings</p>
        </div>

        <div className="commissioner-due-settings">
          <label>
            <span>Years paid ahead</span>
            <input
              type="number"
              min="0"
              step="1"
              value={paidYearsAhead}
              onChange={(event) => {
                setPaidYearsAhead(event.target.value);
              }}
            />
          </label>

          <p className="commissioner-settings-copy">
            {
              `Track picks from ${Number(league.league_season) + (Number(paidYearsAhead || '0') + 1)} and later.`
            }
          </p>

          <button
            type="button"
            className="button-secondary"
            disabled={savingSettings}
            onClick={() => {
              void onSaveSettings(
                league.league_id,
                Math.max(
                  0,
                  Number(paidYearsAhead) || 0,
                ),
              );
            }}
          >
            {
              savingSettings
                ? 'Saving...'
                : 'Save settings'
            }
          </button>
        </div>
      </section>

      <section className="commissioner-section">
        <div className="commissioner-section-header">
          <p>League notes</p>
        </div>

        <div className="commissioner-note-editor">
          <textarea
            value={note}
            onChange={(event) => {
              setNote(event.target.value);
            }}
            placeholder="League notes, roster plans, and reminders..."
          />

          <button
            type="button"
            className="button-secondary"
            disabled={savingNote}
            onClick={() => {
              void onSaveNote(
                league.league_id,
                note,
              );
            }}
          >
            {
              savingNote
                ? 'Saving...'
                : 'Save notes'
            }
          </button>
        </div>
      </section>

      <section className="commissioner-section">
        <div className="commissioner-section-header">
          <p>Future pick dues</p>
        </div>

        <div className="commissioner-list">
          {
            league.dues.length > 0
              ? league.dues.map((entry) => {
                  const key = `${entry.roster_id}-${entry.season}`;
                  const draft = duesDrafts[key] ?? {
                    amount: '',
                    isPaid: entry.is_paid,
                  };

                  return (
                    <div
                      key={key}
                      className="commissioner-due-row"
                    >
                      <div className="commissioner-due-copy">
                        <strong>
                          {entry.roster_name}
                        </strong>
                        <span>
                          {entry.season} dues · {entry.traded_pick_count} future pick trade{entry.traded_pick_count === 1 ? '' : 's'}
                        </span>
                        {
                          entry.traded_pick_labels.length > 0
                            ? (
                              <ul className="commissioner-due-picks">
                                {
                                  entry.traded_pick_labels.map((pickLabel) => (
                                    <li key={`${key}-${pickLabel}`}>
                                      {pickLabel}
                                    </li>
                                  ))
                                }
                              </ul>
                            )
                            : null
                        }
                      </div>

                      <div className="commissioner-due-controls">
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={draft.amount}
                          placeholder="Buy-in"
                          onChange={(event) => {
                            setDuesDrafts((current) => ({
                              ...current,
                              [key]: {
                                ...draft,
                                amount: event.target.value,
                              },
                            }));
                          }}
                        />

                        <label className="commissioner-due-toggle">
                          <input
                            type="checkbox"
                            checked={draft.isPaid}
                            onChange={(event) => {
                              setDuesDrafts((current) => ({
                                ...current,
                                [key]: {
                                  ...draft,
                                  isPaid: event.target.checked,
                                },
                              }));
                            }}
                          />
                          <span>Paid</span>
                        </label>

                        <button
                          type="button"
                          className="button-secondary"
                          disabled={!!(savingDuesMap && savingDuesMap[key]) || savingDues}
                          onClick={() => {
                            const parsedAmount = draft.amount.trim()
                              ? Number(draft.amount)
                              : null;

                            void onSaveDues(
                              entry,
                              Number.isFinite(parsedAmount)
                                ? parsedAmount
                                : null,
                              draft.isPaid,
                            );
                          }}
                        >
                          {
                            (savingDuesMap && savingDuesMap[key]) || savingDues
                              ? 'Saving...'
                              : 'Save'
                          }
                        </button>
                      </div>
                    </div>
                  );
                })
              : (
                <div className="commissioner-empty-note">
                  No future traded picks detected for dues tracking.
                </div>
              )
          }
        </div>
      </section>
    </article>
  );
}


export const CommissionerPage = () => {
  const navigate = useNavigate();
  const params = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const valuePreference = useValuePreference();
  const auth = useAuth();
  const connection = useSleeperConnection();

  const routeUsername = params.username ?? null;
  const activeUsername = routeUsername ?? connection.username ?? null;
  const [usernameInput, setUsernameInput] = useState(
    activeUsername ?? '',
  );

  useEffect(() => {
    setUsernameInput(activeUsername ?? '');
  }, [activeUsername]);

  const activeTab = (
    searchParams.get('tab') === 'workspace'
      ? 'workspace'
      : searchParams.get('tab') === 'cutdowns'
      ? 'cutdowns'
      : 'orphans'
  ) as CommissionerTab;

  const valueBasis = isValueBasis(
    searchParams.get('basis'),
  )
    ? (searchParams.get('basis') as ValueBasis)
    : valuePreference.preference;

  const orphans = useCommissionerOrphans(
    activeUsername,
    valueBasis,
  );
  const canManageWorkspace = (
    Boolean(connection.username)
    && activeUsername === connection.username
  );
  const workspace = useCommissionerWorkspace(
    canManageWorkspace,
  );
  const saveNoteMutation = useSaveCommissionerNote();
  const saveDuesMutation = useSaveCommissionerDues();
  const saveSettingsMutation = useSaveCommissionerSettings();

  const [savingNoteByLeague, setSavingNoteByLeague] = useState<Record<string, boolean>>({});
  const [savingDuesByLeague, setSavingDuesByLeague] = useState<Record<string, boolean>>({});
  const [savingDuesByEntry, setSavingDuesByEntry] = useState<Record<string, boolean>>({});
  const [savingSettingsByLeague, setSavingSettingsByLeague] = useState<Record<string, boolean>>({});

  const shareUrl = useMemo(() => {
    if (!activeUsername) {
      return '';
    }

    return `${window.location.origin}/commissioner/${encodeURIComponent(activeUsername)}?tab=${activeTab}&basis=${valueBasis}`;
  }, [
    activeTab,
    activeUsername,
    valueBasis,
  ]);

  const setTab = (tab: CommissionerTab) => {
    const next = new URLSearchParams(searchParams);
    next.set('tab', tab);
    next.set('basis', valueBasis);
    setSearchParams(next);
  };

  const setBasis = (nextBasis: ValueBasis) => {
    const next = new URLSearchParams(searchParams);
    next.set('tab', activeTab);
    next.set('basis', nextBasis);
    setSearchParams(next);
  };

  const handleOpen = () => {
    const trimmed = usernameInput.trim();

    if (!trimmed) {
      return;
    }

    navigate(
      `/commissioner/${encodeURIComponent(trimmed)}?tab=${activeTab}&basis=${valueBasis}`,
    );
  };

  const handleSaveNote = async (
    leagueId: string,
    note: string,
  ) => {
    setSavingNoteByLeague((s) => ({ ...s, [leagueId]: true }));
    try {
      await saveNoteMutation.mutateAsync({
        league_id: leagueId,
        note,
      });
      notify.success('League notes saved.');
    } catch {
      notify.error('Unable to save league notes.');
    } finally {
      setSavingNoteByLeague((s) => ({ ...s, [leagueId]: false }));
    }
  };

  const handleSaveDues = async (
    entry: CommissionerLeagueDuesEntry,
    buyInAmount: number | null,
    isPaid: boolean,
  ) => {
    const leagueId = entry.league_id;
    const entryKey = `${entry.roster_id}-${entry.season}`;
    setSavingDuesByEntry((s) => ({ ...s, [entryKey]: true }));
    try {
      await saveDuesMutation.mutateAsync({
        league_id: entry.league_id,
        roster_id: entry.roster_id,
        season: entry.season,
        buy_in_amount: buyInAmount,
        is_paid: isPaid,
      });
      notify.success('League dues updated.');
    } catch {
      notify.error('Unable to save league dues.');
    } finally {
      setSavingDuesByEntry((s) => ({ ...s, [entryKey]: false }));
      // keep per-league flag for disabling entire league if needed
      setSavingDuesByLeague((s) => ({ ...s, [leagueId]: false }));
    }
  };

  const handleSaveSettings = async (
    leagueId: string,
    paidYearsAhead: number,
  ) => {
    setSavingSettingsByLeague((s) => ({ ...s, [leagueId]: true }));
    try {
      await saveSettingsMutation.mutateAsync({
        league_id: leagueId,
        paid_years_ahead: paidYearsAhead,
      });
      notify.success('Dues settings updated.');
    } catch {
      notify.error('Unable to save dues settings.');
    } finally {
      setSavingSettingsByLeague((s) => ({ ...s, [leagueId]: false }));
    }
  };

  return (
    <main className="commissioner-page">
      <section className="page-header">
        <div>
          <p className="page-eyebrow">Commissioner</p>
          <h1 className="page-title">
            Commissioner board
          </h1>
          <p className="page-description">
            Review public orphan rosters, league settings, starting lineup
            strength, and draft capital from a shareable Sleeper username URL.
          </p>
        </div>

        <div className="commissioner-toolbar">
          <label className="commissioner-username-control">
            <span>Sleeper username</span>

            <div className="commissioner-username-row">
              <input
                value={usernameInput}
                onChange={(event) => {
                  setUsernameInput(event.target.value);
                }}
                placeholder="Enter Sleeper username"
              />

              <button
                className="button-primary"
                type="button"
                onClick={handleOpen}
              >
                Open
              </button>
            </div>
          </label>

          <label className="waivers-value-selector">
            <span>Value Basis</span>

            <select
              value={valueBasis}
              onChange={(event) => {
                setBasis(
                  event.target.value as ValueBasis,
                );
              }}
            >
              {
                getValueBasisOptions(auth.isLoggedIn).map((option) => (
                  <option
                    key={option.value}
                    value={option.value}
                  >
                    {option.label}
                  </option>
                ))
              }
            </select>
          </label>

          {
            shareUrl && activeTab === 'orphans'
              ? (
                <button
                  className="button-secondary"
                  type="button"
                  onClick={() => {
                    void navigator.clipboard.writeText(
                      shareUrl,
                    );
                  }}
                >
                  Copy link
                </button>
              )
              : null
          }
        </div>
      </section>

      <div className="commissioner-tabs" role="tablist" aria-label="Commissioner tabs">
        <button
          className={
            activeTab === 'orphans'
              ? 'commissioner-tab-button active'
              : 'commissioner-tab-button'
          }
          type="button"
          onClick={() => {
            setTab('orphans');
          }}
        >
          Available Orphans
        </button>
        {
          canManageWorkspace
            ? (
              <button
                className={
                  activeTab === 'workspace'
                    ? 'commissioner-tab-button active'
                    : 'commissioner-tab-button'
                }
                type="button"
                onClick={() => {
                  setTab('workspace');
                }}
              
              >
                League Dues Tracker
              </button>
            )
            : null
        }
        {
          canManageWorkspace
            ? (
              <button
                className={
                  activeTab === 'cutdowns'
                    ? 'commissioner-tab-button active'
                    : 'commissioner-tab-button'
                }
                type="button"
                onClick={() => {
                  setTab('cutdowns');
                }}
              >
                Roster Cutdowns
              </button>

            )
            : null
        }
      </div>

      {
        !activeUsername
          ? (
            <div className="commissioner-empty-state">
              Enter a Sleeper username or link an account to open a shareable commissioner view.
            </div>
          )
          : null
      }

      {
        activeTab === 'orphans' && activeUsername && orphans.loading
          ? (
            <CommissionerCardGridSkeleton mode="orphans" />
          )
          : null
      }

      {
        activeTab === 'orphans' && activeUsername && !orphans.loading && orphans.error
          ? (
            <div className="commissioner-empty-state">
              Unable to load commissioner data for "{activeUsername}".
            </div>
          )
          : null
      }

      {
        activeTab === 'orphans' && activeUsername && !orphans.loading && orphans.data && orphans.data.orphans.length === 0
          ? (
            <div className="commissioner-empty-state">
              No orphan rosters found for "{activeUsername}".
            </div>
          )
          : null
      }

      {
        activeTab === 'orphans' && activeUsername && orphans.data && orphans.data.orphans.length > 0
          ? (
            <section className="commissioner-card-grid">
              {
                orphans.data.orphans.map((orphan) => (
                  <CommissionerOrphanCard
                    key={`${orphan.league_id}-${orphan.roster_id}`}
                    orphan={orphan}
                    valueBasis={valueBasis}
                  />
                ))
              }
            </section>
          )
          : null
      }

      {
        activeTab === 'workspace' && !canManageWorkspace
          ? (
            <div className="commissioner-empty-state">
              Link your Sleeper account and open your own username to use the league dues tracker.
            </div>
          )
          : null
      }

      {
        activeTab === 'workspace' && canManageWorkspace && workspace.loading
          ? (
            <CommissionerCardGridSkeleton mode="workspace" />
          )
          : null
      }

      {
        activeTab === 'workspace' && canManageWorkspace && !workspace.loading && workspace.error
          ? (
            <div className="commissioner-empty-state">
              Unable to load your league dues tracker.
            </div>
          )
          : null
      }

      {
        activeTab === 'workspace' && workspace.data
          ? (
            <section className="commissioner-card-grid">
              {
                workspace.data.leagues.map((league) => (
                  <CommissionerWorkspaceCard
                    key={league.league_id}
                    league={league}
                    onSaveNote={handleSaveNote}
                    onSaveDues={handleSaveDues}
                    onSaveSettings={handleSaveSettings}
                    savingNote={!!savingNoteByLeague[league.league_id]}
                    savingDues={!!savingDuesByLeague[league.league_id]}
                    savingDuesMap={savingDuesByEntry}
                    savingSettings={!!savingSettingsByLeague[league.league_id]}
                  />
                ))
              }
            </section>
          )
          : null
      }

      {
        activeTab === 'cutdowns' && (
          <CommissionerCutdownsTab canManageWorkspace={canManageWorkspace} />
        )
      }
    </main>

  );
};
