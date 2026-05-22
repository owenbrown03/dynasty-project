import { useState } from 'react';
import { useNavigate, useOutletContext } from 'react-router'; 
import toast from 'react-hot-toast';

import './UsernameInput.css';
import { useUserContext } from '../../context/UserContext';
import { useSleeperSync } from '@/hooks/useSleeperSync';
import { notify } from '@/utils/notify';

interface DashboardContext {
  pendingSync: string | null;
  handleSyncAttempt: (name: string | null) => boolean;
}

export function UsernameInput() {
  const [inputText, setInputText] = useState('');
  const { username, setUsername } = useUserContext(); 
  const { pendingSync, handleSyncAttempt } = useOutletContext<DashboardContext>();
  const navigate = useNavigate();

  const { performSync, isSyncing } = useSleeperSync();
  async function submitUsername() {
    const trimmed = inputText.trim();
    if (!trimmed || isSyncing) return;   
    const loadingToast = notify.loading("Syncing profile...");
    try {
      await performSync(trimmed);
      setUsername(trimmed);
      const isSyncComplete = handleSyncAttempt(trimmed);
      
      if (isSyncComplete) {
        notify.success("Connected successfully!");
        navigate(`/dashboard`);
      } else {
        notify.success("Profile synced! Please log in to finalize.");
      }
    } catch (err) {
      notify.error("Failed to sync. Please try again.");
    } finally {
      toast.dismiss(loadingToast);
    }
  }

  function saveUsername(event: React.ChangeEvent<HTMLInputElement>) {
    setInputText(event.target.value);
  }

  return (
     <div>
      <div className="input-container">
        <input
          placeholder="Sleeper username"
          size={30}
          onChange={saveUsername}
          value={inputText}
          className="username-input"
          onKeyDown={(e) => e.key === 'Enter' && submitUsername()} 
        />
        <button
          onClick={submitUsername}
          className="submit-button"
          disabled={isSyncing}
        >
          {isSyncing ? "Syncing..." : "Submit"}
        </button>
      </div>
      <div>
        {isSyncing && (
          <p>
            ⏳ Pulling league profiles and checking rosters for "{inputText.trim() || username}"...
          </p>
        )}

        {!isSyncing && pendingSync && (
          <p className="auth-prompt">
            🔐 Please log in to complete the sync for "<strong>{pendingSync}</strong>".
          </p>
        )}
              
        {!isSyncing && !pendingSync && username && (
          <p>
            ✅ Connected profile: <strong>{username}</strong>
          </p>
        )}
      </div>
    </div> 
  );
}