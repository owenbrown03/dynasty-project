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

export function CommissionerCutdownsTab({
  canManageWorkspace,
}: {
  canManageWorkspace: boolean;
}) {
  const { data: leagues, loading, error } = useCommissionerCutdowns(canManageWorkspace);
  const actionMutation = useExecuteCommissionerCutdownAction();

  const [selectedRosters, setSelectedRosters] = useState<Record<string, number[]>>({});
  const [actionType, setActionType] = useState<string>('notify');
  const [customMessage, setCustomMessage] = useState<string>('');

  if (!canManageWorkspace) {
    return (
      <div className="commissioner-empty-state">
        Link your Sleeper account and open your own username to use the cutdowns tracker.
      </div>
    );
  }

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
    const leagueIds = Object.keys(selectedRosters).filter(id => selectedRosters[id].length > 0);
    if (leagueIds.length === 0) {
      notify.error('Select at least one roster to execute an action.');
      return;
    }

    try {
      await actionMutation.mutateAsync({
        league_ids: leagueIds,
        action_type: actionType,
        custom_message: customMessage || null,
        selected_roster_ids: selectedRosters,
      });
      notify.success('Action executed successfully.');
      setSelectedRosters({});
      setCustomMessage('');
    } catch {
      notify.error('Failed to execute action.');
    }
  };

  return (
    <div className="commissioner-cutdowns-tab">
      <div className="cutdowns-controls">
        <div className="cutdowns-actions">
          <label>
            <span>Action</span>
            <select
              value={actionType}
              onChange={(e) => setActionType(e.target.value)}
            >
              <option value="notify">Notify Managers</option>
              <option value="force_drop">Force Drop Lowest KTC Value Players</option>
            </select>
          </label>
          {actionType === 'notify' && (
            <label>
              <span>Custom Message (Optional)</span>
              <input
                type="text"
                value={customMessage}
                onChange={(e) => setCustomMessage(e.target.value)}
                placeholder="Message to include..."
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
