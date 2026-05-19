import { useState } from 'react';
import { useNavigate } from 'react-router'; 

import './UsernameInput.css';
import { useUserContext } from '../../context/UserContext';
import { useUserSync, useLeaguemateSync } from '../../hooks/usernameHandler'

export function UsernameInput() {
  const [inputText, setInputText] = useState('');
  const navigate = useNavigate();
  const { username, setUsername } = useUserContext(); 
  const { loading: userSyncing } = useUserSync(username ?? undefined);
  const { loading: matesSyncing } = useLeaguemateSync(username ?? undefined);

  function saveUsername(event: React.ChangeEvent<HTMLInputElement>) {
    setInputText(event.target.value);
  }

  function submitUsername() {
    const trimmedUsername = inputText.trim();
    if (!trimmedUsername) return;
    setUsername(trimmedUsername);
    navigate(`/dashboard/${trimmedUsername}`);
  }

  const isSyncing = userSyncing || matesSyncing;
  
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
        >
          Submit
        </button>
      </div>
      <div>
        {isSyncing && (
          <p>
            ⏳ Pulling league profiles and checking rosters for "{inputText.trim() || username}"...
          </p>
        )}
        
        {!isSyncing && username && (
          <p >
            ✅ Connected profile: <strong>{username}</strong>
          </p>
        )}
      </div>
    </div> 
  );
}