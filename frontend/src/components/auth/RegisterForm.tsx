import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';

import './AuthModal.css';
import { api } from '@/api/v1/endpoints';
import { type AuthFormProps } from '@/components/auth/AuthModal';
import { type Login } from '@/types/index';

export const RegisterForm = ({onSwitchView, onClose}: AuthFormProps) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const registerMutation = useMutation({
    mutationFn: api.auth.register,
    onSuccess: () => {
      onClose();
    },
  });

  const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();

    try {
      await registerMutation.mutateAsync(getLoginPayload);
    } catch (err) {
      console.error('Registration failed', err);
    }
  };

  const getLoginPayload = (): Login => ({
    email,
    password,
  });

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <h2>Create Account</h2>

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

      <button type="submit" disabled={registerMutation.isPending}>
        {registerMutation.isPending ? 'Creating...' : 'Register'}
      </button>

      <p>
        Already have an account?
        <span onClick={onSwitchView} className="link"> Login</span>
      </p>
    </form>
  );
};