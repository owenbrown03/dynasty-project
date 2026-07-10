import { useState } from 'react';

import './AuthModal.css';

interface Props {
  onLogin: (
    username: string,
    password: string,
  ) => Promise<void> | void;

  onSwitchView: () => void;

  loading?: boolean;
}

export const LoginForm = ({
  onLogin,
  onSwitchView,
  loading,
}: Props) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (
    e: React.SubmitEvent<HTMLFormElement>,
  ) => {
    e.preventDefault();

    await onLogin(email, password);
  };

  return (
    <form onSubmit={handleSubmit} className="auth-form">
      <h2>Login</h2>

      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />

      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />

      <button
        type="submit"
        className="button-primary"
        disabled={loading}
      >
        {loading
          ? 'Logging in...'
          : 'Log in'}
      </button>

      <p>
        Don't have an account?
        <span onClick={onSwitchView} className="link"> Register</span>
      </p>
    </form>
  );
};
