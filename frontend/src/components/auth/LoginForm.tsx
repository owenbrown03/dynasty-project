import { useState } from 'react';
import './AuthModal.css';
import { api } from '@/api/v1/endpoints';
import { useMutation } from '@/hooks/useMutation';
import { type AuthFormProps } from '@/components/auth/AuthModal';

export const LoginForm = ({ onSwitchView, onClose, onLogin }: AuthFormProps) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const loginMutation = useMutation('user-login', api.auth.login);
  const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>) => {
    console.log('Entering handleSubmit in LoginForm');
    e.preventDefault();
    try {
      await loginMutation.mutateAsync({ email, password });
      await onLogin();
      onClose();
      console.log('Login successful!');
    } catch (err) {
      console.error('Login failed', err);
    }
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
      
      <button type="submit" disabled={loginMutation.loading}>
        {loginMutation.loading ? 'Signing In...' : 'Sign In'}
      </button>
      
      <p>
        Don't have an account? 
        <span onClick={onSwitchView} className="link"> Register</span>
      </p>
    </form>
  );
};