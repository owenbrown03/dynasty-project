import { useState } from 'react';
import { useUsernameOnboarding } from '@/hooks/app/useUsernameOnboarding';

export function UsernameInput() {
  const [input, setInput] = useState('');

  const {
    status,
    submitUsername,
    username,
  } = useUsernameOnboarding();

  return (
    <div>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && submitUsername(input)}
      />

      <button onClick={() => submitUsername(input)}>
        Submit
      </button>

      {status === 'syncing' && <p>Syncing...</p>}
      {status === 'auth-required' && <p>Please log in</p>}
      {status === 'sleeper-linking' && <p>Link Sleeper account</p>}
      {status === 'complete' && <p>Ready: {username}</p>}
    </div>
  );
}