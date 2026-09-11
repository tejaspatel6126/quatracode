/**
 * login.js — Login page logic.
 */
'use strict';

(async () => {
  // If already authenticated → go to dashboard
  const r = await ApiClient.auth.me();
  if (r.ok && r.data?.data?.user) {
    window.location.href = '/dashboard.html';
    return;
  }

  const form     = UI.$id('login-form');
  const btn      = UI.$id('login-btn');
  const alert_   = UI.$id('login-alert');
  const emailErr = UI.$id('email-error');
  const passErr  = UI.$id('password-error');

  form.addEventListener('submit', async e => {
    e.preventDefault();
    UI.hideAlert(alert_);
    UI.hide(emailErr);
    UI.hide(passErr);

    const email    = form.email.value.trim();
    const password = form.password.value;

    // Basic UX validation (not a security boundary)
    let valid = true;
    if (!email) {
      UI.setText(emailErr, 'Please enter your email address.');
      UI.show(emailErr);
      valid = false;
    }
    if (!password) {
      UI.setText(passErr, 'Please enter your password.');
      UI.show(passErr);
      valid = false;
    }
    if (!valid) return;

    // Disable button during request
    btn.disabled = true;
    btn.classList.add('btn-loading');
    UI.setText(btn, 'Signing in…');

    const result = await Auth.login(email, password);

    btn.disabled = false;
    btn.classList.remove('btn-loading');
    UI.setText(btn, 'Sign In');

    if (result.ok) {
      window.location.href = '/dashboard.html';
    } else {
      UI.showAlert(alert_, result.error || 'Invalid email or password.', 'error');
      form.password.value = '';
      form.email.focus();
    }
  });
})();
