import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import toast from 'react-hot-toast';

import './UsernameInput.css';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';

export function UsernameInput() {
  const connection = useSleeperConnection();
  const [input, setInput] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    setInput(connection.username ?? '');
  }, [connection.username]);

  const submit = async () => {
    const nextUsername = input.trim();
    if (!nextUsername) return;

    await toast.promise(
      connection.upsertConnection(nextUsername),
      {
        loading: 'Syncing profile...',
        success: 'Profile synced!',
        error: 'Failed to sync username',
      }
    );

    navigate('/dashboard');
  };

  return (
    <div className="input-container">
      <input
        className="username-input"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && submit()}
        placeholder="Sleeper username"
      />

      <button
        className="submit-button"
        onClick={submit}
      >
        Submit
      </button>
    </div>
  );
}