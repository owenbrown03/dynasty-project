import { useState } from 'react';
import './AuthModal.css';
import { api } from '@/api/v1/endpoints';
import { useMutation } from '@/hooks/useMutation';
import { type AuthFormProps } from '@/components/auth/AuthModal';

export const RegisterForm = ({ onSwitchView, onClose, onLogin }: AuthFormProps) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const registerMutation = useMutation('user-register', api.auth.register);
  const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>) => {
    console.log('Entering handleSubmit in RegisterForm');
    e.preventDefault();
    try {
      await registerMutation.mutateAsync({ email, password });
      await onLogin();
      onClose();
      console.log('Registration successful! Automatically logged in');
    } catch (err) {
      console.error('Registration failed', err);
    }
  };

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <h2>Create Account</h2>
      <input 
        type="email" 
        placeholder="Email" 
        value={email}
        onChange={(e) => setEmail(e.target.value)} 
      />
      <input 
        type="password" 
        placeholder="Password" 
        value={password}
        onChange={(e) => setPassword(e.target.value)} 
      />
      
      {/* 3. Use the loading state from the mutation hook */}
      <button type="submit" disabled={registerMutation.loading}>
        {registerMutation.loading ? 'Creating...' : 'Register'}
      </button>
      
      <p>
        Already have an account? 
        <span onClick={onSwitchView} className="link"> Login</span>
      </p>
    </form>
  );
};