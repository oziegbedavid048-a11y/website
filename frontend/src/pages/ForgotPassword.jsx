import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ArrowLeft, CircleCheckBig, KeyRound, Loader2, Lock, ShieldCheck } from 'lucide-react';
import { api } from '../lib/api.js';
import { emailOk, passwordOk, passwordRules } from '../lib/validation.js';
import { FormAlert, PasswordField, RuleList, TextField } from '../components/Form.jsx';
import { Logo } from '../components/ui.jsx';

/** Forgotten password: email, then the code from the email and a new password, then sign in. */
export default function ForgotPassword() {
  const location = useLocation();
  const [step, setStep] = useState('email'); // email -> reset -> done
  const [email, setEmail] = useState(location.state?.email || '');
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [alert, setAlert] = useState('');
  const [notice, setNotice] = useState('');
  const [devCode, setDevCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [wait, setWait] = useState(0);

  useEffect(() => {
    document.title = 'Reset your password | Zentra Direct';
  }, []);

  useEffect(() => {
    if (wait <= 0) return undefined;
    const t = setTimeout(() => setWait((w) => w - 1), 1000);
    return () => clearTimeout(t);
  }, [wait]);

  const sendCode = async (e) => {
    e?.preventDefault();
    if (!emailOk(email)) {
      setErrors({ email: 'Enter a valid email address.' });
      return;
    }
    setBusy(true);
    setAlert('');
    setErrors({});
    try {
      const data = await api('/auth/password/forgot/', { method: 'POST', body: { email: email.trim() } });
      setNotice(data.message);
      setDevCode(data.dev_code || '');
      setWait(data.resend_in || 45);
      setStep('reset');
    } catch (err) {
      if (err.errors?.email) setErrors({ email: err.errors.email[0] });
      else setAlert(err.message);
    } finally {
      setBusy(false);
    }
  };

  const reset = async (e) => {
    e.preventDefault();
    const errs = {};
    if (!/^\d{6}$/.test(code)) errs.code = 'Enter the 6-digit code from the email.';
    if (!passwordOk(password, email)) errs.password = 'Choose a password that meets every rule below.';
    setErrors(errs);
    setAlert('');
    if (Object.keys(errs).length) return;
    setBusy(true);
    try {
      await api('/auth/password/reset/', { method: 'POST', body: { email: email.trim(), code, password } });
      setPassword('');
      setStep('done');
    } catch (err) {
      setErrors({
        code: err.errors?.code?.[0],
        password: err.errors?.password?.join(' '),
      });
      if (!err.errors?.code && !err.errors?.password) setAlert(err.message);
      if (err.errors?.code) setCode('');
    } finally {
      setBusy(false);
    }
  };

  return (
    <main id="main" className="auth">
      <aside className="auth__aside">
        <Link to="/" className="auth__logo"><Logo light /></Link>
        <div className="auth__aside-copy">
          <h1>Reset your password</h1>
          <p>We will email you a code so you can choose a new password. It only takes a minute.</p>
          <ul className="auth__points">
            <li><ShieldCheck size={20} aria-hidden="true" /> Your connection is encrypted</li>
            <li><Lock size={20} aria-hidden="true" /> We will never ask for your password by email or phone</li>
          </ul>
        </div>
      </aside>

      <section className="auth__main">
        <div className="auth__card">
          <Link to="/" className="auth__logo auth__logo--mobile"><Logo /></Link>

          {step === 'email' && (
            <>
              <h2>Forgot your password?</h2>
              <p className="auth__sub">Enter the email you use for Zentra Direct and we will send you a 6-digit code.</p>
              <FormAlert>{alert}</FormAlert>
              <form onSubmit={sendCode} noValidate className="auth__form">
                <TextField label="Email" name="email" type="email" maxLength={254} value={email}
                  onChange={(k, v) => { setEmail(v); setErrors({}); }} error={errors.email}
                  autoComplete="username" inputMode="email" autoFocus required />
                <button type="submit" className="btn btn--primary btn--block" disabled={busy}>
                  {busy ? <><Loader2 size={18} className="spin" aria-hidden="true" /> Sending…</> : 'Send code'}
                </button>
              </form>
            </>
          )}

          {step === 'reset' && (
            <>
              <h2>Choose a new password</h2>
              <p className="auth__sub" role="status">{notice}</p>
              <FormAlert>{alert}</FormAlert>
              {devCode && (
                <p className="su-dev" role="note">Development mode: no email is sent. Your code is <b>{devCode}</b>.</p>
              )}
              <form onSubmit={reset} noValidate className="auth__form">
                <TextField label="6-digit code" name="code" value={code} error={errors.code}
                  onChange={(k, v) => { setCode(v.replace(/\D/g, '').slice(0, 6)); setErrors((x) => ({ ...x, code: undefined })); }}
                  inputMode="numeric" autoComplete="one-time-code" maxLength={6} placeholder="123456"
                  className="auth__code" autoFocus required />
                <PasswordField label="New password" value={password} error={errors.password}
                  onChange={(k, v) => { setPassword(v); setErrors((x) => ({ ...x, password: undefined })); }}
                  autoComplete="new-password" describedBy="reset-rules" />
                <div className="pw-box">
                  <p>Make sure it does not contain personal information.</p>
                  <RuleList id="reset-rules" rules={passwordRules} value={password} />
                </div>
                <button type="submit" className="btn btn--primary btn--block" disabled={busy}>
                  {busy ? <><Loader2 size={18} className="spin" aria-hidden="true" /> Saving…</> : <><KeyRound size={18} aria-hidden="true" /> Reset password</>}
                </button>
              </form>
              <p className="auth__resend">
                Did not get it? Check your spam folder.{' '}
                <button type="button" className="text-btn" onClick={() => sendCode()} disabled={busy || wait > 0}>
                  {wait > 0 ? `Send a new code in ${wait}s` : 'Send a new code'}
                </button>
              </p>
              <button type="button" className="text-btn auth__back"
                onClick={() => { setStep('email'); setCode(''); setPassword(''); setErrors({}); setAlert(''); }}>
                <ArrowLeft size={16} aria-hidden="true" /> Use a different email
              </button>
            </>
          )}

          {step === 'done' && (
            <div className="auth__done" role="status">
              <CircleCheckBig size={44} aria-hidden="true" className="auth__done-icon" />
              <h2>Password reset</h2>
              <p className="auth__sub">Your password has been changed and you have been signed out on all devices. Sign in with your new password.</p>
              <Link to="/sign-in" className="btn btn--primary btn--block">Sign in</Link>
            </div>
          )}

          {step !== 'done' && (
            <p className="auth__sub auth__foot">Remembered it? <Link to="/sign-in">Back to sign in</Link></p>
          )}
        </div>
      </section>
    </main>
  );
}
