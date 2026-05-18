import { useState } from 'react';
import { useNavigate } from 'react-router'; 

import './UsernameInput.css';
import { useUserContext } from '../../context/UserContext'; 

export function UsernameInput() {
  const [inputText, setInputText] = useState('');
  const navigate = useNavigate();
  const { setUsername } = useUserContext(); 

  function saveUsername(event: React.ChangeEvent<HTMLInputElement>) {
    setInputText(event.target.value);
  }

  function submitUsername() {
    const trimmedUsername = inputText.trim();
    if (!trimmedUsername) return;
    setUsername(trimmedUsername);
    navigate(`/dashboard/${trimmedUsername}`);
  }

  return (
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
  );
}