import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';

import './AuthModal.css';
import { api } from '@/api/v1/endpoints';
import { type AuthFormProps } from '@/components/auth/AuthModal';
import { type Login } from '@/types/index';

export const LoginForm = ({ onSwitchView, onClose }: AuthFormProps) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const loginMutation = useMutation({
    mutationFn: api.auth.login,
    onSuccess: () => {
      onClose();
    },
  });

  const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();

    try {
      await loginMutation.mutateAsync(getLoginPayload());
    } catch (err) {
      console.error('Login failed', err);
    }
  };

  const getLoginPayload = (): Login => ({
    email,
    password,
  });

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

      <button type="submit" disabled={loginMutation.isPending}>
        {loginMutation.isPending ? 'Signing In...' : 'Sign In'}
      </button>

      <p>
        Don't have an account?
        <span onClick={onSwitchView} className="link"> Register</span>
      </p>
    </form>
  );
};