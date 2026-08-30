import { useState, useMemo } from 'react';
import { useCommissionerFaabOverview, useResetCommissionerFaab } from '@/hooks/sleeper/useUsers';
import { notify } from '@/utils/notify';
import { Skeleton } from '@/components/feedback/Skeleton';

export const CommissionerFaabTab = () => {
  const { data: leagues = [], isLoading, error } = useCommissionerFaabOverview();
  const resetMutation = useResetCommissionerFaab();

  const [search, setSearch] = useState('');
  const [onlySpent, setOnlySpent] = useState(false);
  const [selectedLeagues, setSelectedLeagues] = useState<Set<string>>(new Set());
  const [targetBudget, setTargetBudget] = useState<string>('');
  const [useDefault, setUseDefault] = useState(true);

  const filteredLeagues = useMemo(() => {
    return leagues.filter((league) => {
      const matchSearch = league.league_name.toLowerCase().includes(search.toLowerCase());
      const matchSpent = onlySpent ? league.rosters_with_spent_faab > 0 : true;
      return matchSearch && matchSpent;
    });
  }, [leagues, search, onlySpent]);

  const handleSelectAll = () => {
    setSelectedLeagues(new Set(filteredLeagues.map((l) => l.league_id)));
  };

  const handleSelectNone = () => {
    setSelectedLeagues(new Set());
  };

  const toggleLeague = (id: string) => {
    const next = new Set(selectedLeagues);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setSelectedLeagues(next);
  };

  const handleReset = async () => {
    if (selectedLeagues.size === 0) return;
    const confirmed = window.confirm(`Reset FAAB for ${selectedLeagues.size} leagues?`);
    if (!confirmed) return;

    try {
      await resetMutation.mutateAsync({
        league_ids: Array.from(selectedLeagues),
        target_budget: useDefault ? undefined : Number(targetBudget),
      });
      notify.success('FAAB reset successfully');
      setSelectedLeagues(new Set());
    } catch {
      notify.error('Failed to reset FAAB');
    }
  };

  if (isLoading) {
    return <div className="commissioner-empty-state"><Skeleton width={200} height={20} /></div>;
  }

  if (error) {
    return <div className="commissioner-empty-state">Error loading FAAB overview.</div>;
  }

  return (
    <div className="commissioner-faab-tab">
      <div className="commissioner-faab-controls">
        <input 
          type="text" 
          placeholder="Search leagues..." 
          value={search} 
          onChange={e => setSearch(e.target.value)} 
        />
        <label>
          <input 
            type="checkbox" 
            checked={onlySpent} 
            onChange={e => setOnlySpent(e.target.checked)} 
          />
          Only leagues with spent FAAB
        </label>
        <button className="button-secondary" onClick={handleSelectAll}>Select All</button>
        <button className="button-secondary" onClick={handleSelectNone}>Select None</button>
      </div>

      <div className="commissioner-faab-reset-form">
        <label>
          <input 
            type="radio" 
            checked={useDefault} 
            onChange={() => setUseDefault(true)} 
          />
          Reset to default budget
        </label>
        <label>
          <input 
            type="radio" 
            checked={!useDefault} 
            onChange={() => setUseDefault(false)} 
          />
          Custom amount:
        </label>
        <input 
          type="number" 
          disabled={useDefault} 
          value={targetBudget} 
          onChange={e => setTargetBudget(e.target.value)} 
        />
        <button 
          className="button-primary" 
          disabled={selectedLeagues.size === 0 || resetMutation.isPending} 
          onClick={handleReset}
        >
          {resetMutation.isPending ? 'Resetting...' : 'Reset FAAB'}
        </button>
      </div>

      <div className="commissioner-faab-leagues">
        {filteredLeagues.map(league => (
          <div key={league.league_id} className="commissioner-faab-league-card">
            <label>
              <input 
                type="checkbox" 
                checked={selectedLeagues.has(league.league_id)} 
                onChange={() => toggleLeague(league.league_id)} 
              />
              <strong>{league.league_name}</strong>
            </label>
            <div>Default Budget: {league.default_budget}</div>
            <div>Rosters with spent FAAB: {league.rosters_with_spent_faab} / {league.total_rosters}</div>
          </div>
        ))}
        {filteredLeagues.length === 0 && (
          <div className="commissioner-empty-state">No leagues found.</div>
        )}
      </div>
    </div>
  );
};
