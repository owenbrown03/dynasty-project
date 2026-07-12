import { useEffect, useRef } from 'react';

import { useAuth } from '@/hooks/useAuth';

import './EmailVerificationBanner.css';


export function EmailVerificationBanner() {
  const auth = useAuth();
  const didAttemptVerifyRef = useRef(false);
  const isLoggedIn = auth.isLoggedIn;
  const isEmailVerified = auth.isEmailVerified;
  const verifyEmail = auth.verifyEmail;
  const resendVerificationEmail = auth.resendVerificationEmail;
  const isResendingVerificationEmail = (
    auth.isResendingVerificationEmail
  );

  useEffect(() => {
    if (
      !isLoggedIn
      || isEmailVerified
      || didAttemptVerifyRef.current
    ) {
      return;
    }

    const params = new URLSearchParams(
      window.location.search,
    );
    const token = params.get(
      'verify_email_token',
    );

    if (!token) {
      return;
    }

    didAttemptVerifyRef.current = true;

    void verifyEmail(token).finally(() => {
      params.delete('verify_email_token');
      const search = params.toString();
      const nextUrl = search
        ? `${window.location.pathname}?${search}`
        : window.location.pathname;

      window.history.replaceState(
        {},
        '',
        nextUrl,
      );
    });
  }, [
    isEmailVerified,
    isLoggedIn,
    verifyEmail,
  ]);

  if (
    !isLoggedIn
    || isEmailVerified
  ) {
    return null;
  }

  return (
    <section className="email-verification-banner">
      <div>
        <strong>Verify your email</strong>
        <p>
          Check your inbox for the Dynasty Base verification link. If SMTP is
          not configured locally, resend will generate a link for you instead.
        </p>
      </div>

      <button
        type="button"
        className="button-secondary"
        onClick={() => {
          void resendVerificationEmail();
        }}
        disabled={isResendingVerificationEmail}
      >
        {
          isResendingVerificationEmail
            ? 'Sending...'
            : 'Resend email'
        }
      </button>
    </section>
  );
}
