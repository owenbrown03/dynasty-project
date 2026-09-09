import { useMemo, useState } from 'react';
import { Skeleton } from '@/components/feedback/Skeleton';
import { notify } from '@/utils/notify';
import {
  useCommissionerCutdowns,
  useExecuteCommissionerCutdownAction,
} from '@/hooks/sleeper/useUsers';
import type {
  CommissionerCutdownActionResult,
  CommissionerCutdownLeague,
  CommissionerCutdownViolation,
} from '@/types';
import {
  CutdownReviewModal,
  type CutdownRosterPreview,
} from './CutdownReviewModal';

const ACTION_DESCRIPTIONS: Record<string, string> = {
  chat_all: 'Post an announcement mentioning @all in league chat to remind all managers.',
  chat_tag: 'Tag violating managers directly in league chat with the cutdown reminder.',
  dm_warning: 'Send a private direct message (DM) warning to each violating manager.',
  force_drop: 'Commissioner enforcement: forcefully drop the lowest KTC value player(s) on violating rosters.',
};

const ACTION_PLACEHOLDERS: Record<string, string> = {
  chat_all: "@all Friendly reminder from the commissioner: Please check your rosters and cut down...",
  chat_tag: "Optional prefix (e.g. 'Roster Cutdown Reminder:')",
  dm_warning: "Hi @manager, reminder that your roster is over the limit...",
};

export function CommissionerCutdownsTab() {
  const { data: leagues, loading, fetching, error, refetch } = useCommissionerCutdowns(true);
  const actionMutation = useExecuteCommissionerCutdownAction();

  const [selectedRosters, setSelectedRosters] = useState<Record<string, number[]>>({});
  const [actionType, setActionType] = useState<string>('chat_all');
  const [customMessage, setCustomMessage] = useState<string>('');
  const [isReviewOpen, setIsReviewOpen] = useState(false);
  const [actionResults, setActionResults] = useState<CommissionerCutdownActionResult[]>([]);
  const [actionError, setActionError] = useState<Error | null>(null);

  const selectedPreviews: CutdownRosterPreview[] = useMemo(() => {
    if (!leagues) return [];
    const list: CutdownRosterPreview[] = [];
    for (const league of leagues) {
      const selected = selectedRosters[league.league_id] || [];
      if (selected.length === 0) continue;
      for (const v of league.violations) {
        if (selected.includes(v.roster_id)) {
          list.push({
            leagueId: league.league_id,
            leagueName: league.league_name,
            rosterId: v.roster_id,
            ownerName: v.owner_name || `Roster ${v.roster_id}`,
            overLimitCount: v.over_limit_count,
            drops: v.proposed_drops || [],
          });
        }
      }
    }
    return list;
  }, [leagues, selectedRosters]);

  if (loading) {
    return (
      <div className="commissioner-card-grid">
        <Skeleton height={200} />
      </div>
    );
  }

  if (error || !leagues) {
    return (
      <div className="commissioner-empty-state">
        Unable to load cutdowns data.
      </div>
    );
  }

  if (leagues.length === 0) {
    return (
      <div className="commissioner-empty-state">
        No roster cutdown violations detected across your leagues.
      </div>
    );
  }

  const handleToggleRoster = (leagueId: string, rosterId: number) => {
    setSelectedRosters((prev) => {
      const current = prev[leagueId] || [];
      const updated = current.includes(rosterId)
        ? current.filter((id) => id !== rosterId)
        : [...current, rosterId];

      return {
        ...prev,
        [leagueId]: updated,
      };
    });
  };

  const handleActionClick = () => {
    let leagueIds = Object.keys(selectedRosters).filter(id => selectedRosters[id].length > 0);
    if (leagueIds.length === 0) {
      if (actionType === 'chat_all' && leagues && leagues.length > 0) {
        leagueIds = leagues.map((l) => l.league_id);
      } else {
        notify.error('Select at least one roster to execute an action.');
        return;
      }
    }

    if (actionType === 'force_drop') {
      setActionResults([]);
      setActionError(null);
      setIsReviewOpen(true);
      return;
    }

    void executeNonDropAction(leagueIds);
  };

  const executeNonDropAction = async (leagueIds: string[]) => {
    try {
      const res = await actionMutation.mutateAsync({
        league_ids: leagueIds,
        action_type: actionType,
        custom_message: customMessage || null,
        selected_roster_ids: selectedRosters,
      });

      const failures = res.results.filter((r) => !r.success);
      if (failures.length > 0) {
        const errors = failures.map((f) => f.error || `Roster ${f.roster_id || ''} failed`).join('; ');
        notify.error(`Action finished with error(s): ${errors}`);
      } else {
        notify.success('Action executed successfully.');
      }
      setSelectedRosters({});
      setCustomMessage('');
      await refetch();
    } catch {
      notify.error('Failed to execute action.');
    }
  };

  const handleConfirmModalDrops = async () => {
    const leagueIds = Object.keys(selectedRosters).filter(id => selectedRosters[id].length > 0);
    if (leagueIds.length === 0) return;

    try {
      const res = await actionMutation.mutateAsync({
        league_ids: leagueIds,
        action_type: 'force_drop',
        custom_message: null,
        selected_roster_ids: selectedRosters,
      });

      setActionResults(res.results);
      const failures = res.results.filter((r) => !r.success);
      if (failures.length === 0) {
        notify.success('Players force dropped successfully.');
      } else {
        notify.error('Some roster drops failed. Review details below.');
      }
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err : new Error('Failed to execute drops'));
    }
  };

  const handleCloseModal = () => {
    setIsReviewOpen(false);
    if (actionResults.length > 0) {
      setSelectedRosters({});
      void refetch();
    }
    setActionResults([]);
    setActionError(null);
  };

  return (
    <div className="commissioner-cutdowns-tab">
      <div className="cutdowns-controls">
        <div className="cutdowns-controls-row">
          <button
            type="button"
            className="button-secondary"
            onClick={() => refetch()}
            disabled={loading || fetching}
          >
            {fetching ? 'Refreshing...' : 'Refresh Status'}
          </button>

          <div className="cutdowns-actions">
            <label>
              <span>Action</span>
              <select
                value={actionType}
                onChange={(e) => setActionType(e.target.value)}
              >
                <option value="chat_all">@all League Chat Announcement</option>
                <option value="chat_tag">Tag Violators in League Chat</option>
                <option value="dm_warning">Direct Message (DM) Warning</option>
                <option value="force_drop">Force Drop Lowest KTC Players</option>
              </select>
            </label>
            {actionType !== 'force_drop' && (
              <label>
                <span>Custom Message (Optional)</span>
                <input
                  type="text"
                  value={customMessage}
                  onChange={(e) => setCustomMessage(e.target.value)}
                  placeholder={ACTION_PLACEHOLDERS[actionType] || 'Message to include...'}
                />
              </label>
            )}
            <button
              className="button-primary"
              onClick={handleActionClick}
              disabled={actionMutation.isPending}
            >
              {actionType === 'force_drop'
                ? 'Review & Drop'
                : (actionMutation.isPending ? 'Executing...' : 'Execute Action')}
            </button>
          </div>
        </div>
        {ACTION_DESCRIPTIONS[actionType] && (
          <div className="cutdowns-action-description">
            {ACTION_DESCRIPTIONS[actionType]}
          </div>
        )}
      </div>

      <div className="commissioner-card-grid">
        {leagues.map((league: CommissionerCutdownLeague) => (
          <div key={league.league_id} className="commissioner-card">
            <header className="commissioner-card-header">
              <div>
                <p className="commissioner-card-kicker">League</p>
                <h2 className="commissioner-card-title">{league.league_name}</h2>
                <p className="commissioner-card-subtitle">
                  {league.violations.length} violations
                </p>
              </div>
            </header>
            <div className="commissioner-list">
              {league.violations.map((violation: CommissionerCutdownViolation) => {
                const isSelected = (selectedRosters[league.league_id] || []).includes(violation.roster_id);
                return (
                  <div key={violation.roster_id} className="commissioner-due-row">
                    <label className="cutdown-violation-label">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => handleToggleRoster(league.league_id, violation.roster_id)}
                      />
                      <div className="commissioner-due-copy">
                        <strong>{violation.owner_name || `Roster ${violation.roster_id}`}</strong>
                        <span>
                          {violation.roster_size} / {violation.max_roster_size} spots ({violation.over_limit_count} over)
                        </span>
                        {violation.proposed_drops && violation.proposed_drops.length > 0 && (
                          <div className="cutdown-violation-drops-preview">
                            <span className="cutdown-drops-title">Proposed Drops (lowest KTC):</span>
                            <div className="cutdown-drops-pills">
                              {violation.proposed_drops.map(p => (
                                <span key={p.player_id} className="cutdown-drop-pill">
                                  {p.name} ({p.position || '—'}{p.team ? ` · ${p.team}` : ''}){p.ktc_value != null ? ` · ${p.ktc_value.toLocaleString()} KTC` : ''}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </label>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {isReviewOpen && (
        <CutdownReviewModal
          previews={selectedPreviews}
          submitting={actionMutation.isPending}
          results={actionResults}
          error={actionError}
          onClose={handleCloseModal}
          onConfirm={handleConfirmModalDrops}
        />
      )}
    </div>
  );
}
