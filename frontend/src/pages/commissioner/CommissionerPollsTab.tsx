import { useState } from 'react';
import { useCommissionerWorkspace, useBroadcastCommissionerPoll } from '@/hooks/sleeper/useUsers';
import { notify } from '@/utils/notify';
import { CommissionerWorkspaceLeague, CommissionerPollBroadcastResult } from '@/types';

export function CommissionerPollsTab() {
  const { data: workspace, loading } = useCommissionerWorkspace(true);
  const broadcastMutation = useBroadcastCommissionerPoll();

  const [prompt, setPrompt] = useState('');
  const [choices, setChoices] = useState<string[]>(['Yes', 'No']);
  const [isPrivate, setIsPrivate] = useState(true);
  const [expirationDays, setExpirationDays] = useState<number | null>(7);
  const [followUpMessage, setFollowUpMessage] = useState('');
  const [search, setSearch] = useState('');
  
  const [selectedLeagues, setSelectedLeagues] = useState<Set<string>>(new Set());
  
  const [showPreview, setShowPreview] = useState(false);
  const [broadcasting, setBroadcasting] = useState(false);
  const [results, setResults] = useState<CommissionerPollBroadcastResult[] | null>(null);

  if (loading) {
    return <div>Loading leagues...</div>;
  }

  const leagues = workspace?.leagues || [];
  const filteredLeagues = leagues.filter(l => l.league_name.toLowerCase().includes(search.toLowerCase()));

  const toggleLeague = (id: string) => {
    const next = new Set(selectedLeagues);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedLeagues(next);
  };

  const handleBroadcast = async () => {
    if (!prompt.trim() || choices.some(c => !c.trim())) {
      notify.error("Prompt and choices cannot be empty");
      return;
    }
    if (choices.length < 2) {
      notify.error("At least two choices are required");
      return;
    }
    if (selectedLeagues.size === 0) {
      notify.error("Select at least one league");
      return;
    }

    setBroadcasting(true);
    try {
      const res = await broadcastMutation.mutateAsync({
        prompt,
        choices: choices.filter(c => c.trim()),
        is_private: isPrivate,
        expiration_days: expirationDays,
        follow_up_message: followUpMessage || null,
        league_ids: Array.from(selectedLeagues),
      });
      setResults(res.results);
      notify.success(`Broadcast complete: ${res.successful_leagues}/${res.total_leagues} succeeded`);
    } catch (e) {
      notify.error("Error broadcasting polls");
    } finally {
      setBroadcasting(false);
    }
  };

  const resetForm = () => {
    setPrompt('');
    setChoices(['Yes', 'No']);
    setFollowUpMessage('');
    setSelectedLeagues(new Set());
    setShowPreview(false);
    setResults(null);
  }

  return (
    <div className="commissioner-polls-tab">
      {!showPreview && !results && (
        <div className="polls-form">
          <h2>Create Commissioner Poll</h2>
          <label>
            <span>Prompt:</span>
            <input type="text" value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="E.g., Should we move to Superflex?" />
          </label>
          <div className="choices">
            <span>Choices:</span>
            {choices.map((c, i) => (
              <div key={i} className="choice-row">
                <input type="text" value={c} onChange={e => {
                  const next = [...choices];
                  next[i] = e.target.value;
                  setChoices(next);
                }} />
                {choices.length > 2 && (
                  <button type="button" onClick={() => setChoices(choices.filter((_, idx) => idx !== i))}>X</button>
                )}
              </div>
            ))}
            <button type="button" onClick={() => setChoices([...choices, ''])}>+ Add Option</button>
          </div>
          <div className="settings">
            <label>
              <input type="checkbox" checked={isPrivate} onChange={e => setIsPrivate(e.target.checked)} />
              Anonymous (Private) Poll
            </label>
            <label>
              <span>Expiration:</span>
              <select value={expirationDays || ''} onChange={e => setExpirationDays(e.target.value ? Number(e.target.value) : null)}>
                <option value="1">1 Day</option>
                <option value="3">3 Days</option>
                <option value="7">7 Days</option>
                <option value="14">14 Days</option>
                <option value="">No Expiration</option>
              </select>
            </label>
            <label>
              <span>Follow-up Message:</span>
              <textarea value={followUpMessage} onChange={e => setFollowUpMessage(e.target.value)} placeholder="Message to send with the poll..." />
            </label>
          </div>
          
          <div className="league-selection">
            <h3>Target Leagues ({selectedLeagues.size} selected)</h3>
            <input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search leagues..." />
            <button type="button" onClick={() => setSelectedLeagues(new Set(filteredLeagues.map(l => l.league_id)))}>Select All</button>
            <button type="button" onClick={() => setSelectedLeagues(new Set())}>Select None</button>
            
            <ul className="league-list">
              {filteredLeagues.map(l => (
                <li key={l.league_id}>
                  <label>
                    <input type="checkbox" checked={selectedLeagues.has(l.league_id)} onChange={() => toggleLeague(l.league_id)} />
                    {l.league_name} ({l.league_season})
                  </label>
                </li>
              ))}
            </ul>
          </div>
          
          <button type="button" className="button-primary" onClick={() => setShowPreview(true)} disabled={selectedLeagues.size === 0 || !prompt}>
            Review & Broadcast
          </button>
        </div>
      )}

      {showPreview && !results && (
        <div className="polls-preview">
          <h2>Review Broadcast</h2>
          <p><strong>Prompt:</strong> {prompt}</p>
          <p><strong>Choices:</strong> {choices.join(', ')}</p>
          <p><strong>Private:</strong> {isPrivate ? 'Yes' : 'No'}</p>
          <p><strong>Expiration:</strong> {expirationDays ? `${expirationDays} days` : 'None'}</p>
          <p><strong>Follow-up Message:</strong> {followUpMessage}</p>
          <p><strong>Targeting {selectedLeagues.size} leagues.</strong></p>
          <p className="warning">SAFETY WARNING: This will send live polls and messages to all selected leagues immediately. This action cannot be undone.</p>
          <button type="button" onClick={() => setShowPreview(false)} disabled={broadcasting}>Back</button>
          <button type="button" className="button-primary" onClick={handleBroadcast} disabled={broadcasting}>
            {broadcasting ? 'Broadcasting...' : 'Confirm Broadcast'}
          </button>
        </div>
      )}

      {results && (
        <div className="polls-results">
          <h2>Broadcast Results</h2>
          <ul>
            {results.map(r => (
              <li key={r.league_id}>
                {r.league_name || r.league_id}: {r.success ? '✅ Success' : `❌ Failed (${r.error})`}
              </li>
            ))}
          </ul>
          <button type="button" onClick={resetForm}>Create Another Poll</button>
        </div>
      )}
    </div>
  );
}
