import { useState } from 'react'
import './UsernameInput.css';

interface Props {
  setUsername: (name: string) => void;
}

function UsernameInput({ setUsername }: Props) {
  const [inputText, setInputText] = useState('');

  function saveUsername(event: React.ChangeEvent<HTMLInputElement>) {
    setInputText(event.target.value);
  }

  async function submitUsername() {
    const Username = inputText
    setUsername(Username);
    setInputText('');
  }

  return (
    <div className="input-container">
      <input
        placeholder="Sleeper username"
        size={30}
        onChange={saveUsername}
        value={inputText}
        className="username-input"
      />
      <button
        onClick={submitUsername}
        className="submit-button"
      >Submit</button>
    </div>
  );
}

export default UsernameInput;