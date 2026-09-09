import { useState } from 'react';
import { Skeleton } from '@/components/feedback/Skeleton';
import { notify } from '@/utils/notify';
import {
  useCommissionerCutdowns,
  useExecuteCommissionerCutdownAction,
} from '@/hooks/sleeper/useUsers';
import type {
  CommissionerCutdownLeague,
  CommissionerCutdownViolation,
} from '@/types';

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

  const handleExecute = async () => {
    let leagueIds = Object.keys(selectedRosters).filter(id => selectedRosters[id].length > 0);
    if (leagueIds.length === 0) {
      if (actionType === 'chat_all' && leagues && leagues.length > 0) {
        leagueIds = leagues.map((l) => l.league_id);
      } else {
        notify.error('Select at least one roster to execute an action.');
        return;
      }
    }

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

  return (
    <div className="commissioner-cutdowns-tab">
      <div className="cutdowns-controls">
        <button
          type="button"
          className="button-secondary"
          onClick={() => refetch()}
          disabled={loading || fetching}
          style={{ marginRight: 'auto' }}
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
            onClick={() => void handleExecute()}
            disabled={actionMutation.isPending}
          >
            {actionMutation.isPending ? 'Executing...' : 'Execute Action'}
          </button>
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
                      </div>
                    </label>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
