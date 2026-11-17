import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Loader2, Lock, ShieldCheck } from 'lucide-react';
import { useAuth } from '../lib/auth.jsx';
import { emailOk } from '../lib/validation.js';
import { safeNext } from '../lib/safety.js';
import { CheckboxField, FormAlert, PasswordField, TextField, focusFirstError } from '../components/Form.jsx';
import { Logo } from '../components/ui.jsx';

export { safeNext } from '../lib/safety.js';

export default function SignIn() {
  const { signIn, verifySignIn, resendSignIn, user, loading } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = safeNext(params.get('next'));
  const [form, setForm] = useState({ email: '', password: '', remember: true });
  const [errors, setErrors] = useState({});
  const [alert, setAlert] = useState(
    params.get('idle') ? 'You were signed out after 30 minutes without activity. Please sign in again.' : '',
  );
  const [busy, setBusy] = useState(false);
  // After the password: the code we emailed. { email, devCode } while waiting for it.
  const [step, setStep] = useState(null);
  const [code, setCode] = useState('');
  const [wait, setWait] = useState(0);
  const formRef = useRef(null);

  useEffect(() => {
    if (wait <= 0) return undefined;
    const t = setTimeout(() => setWait((w) => w - 1), 1000);
    return () => clearTimeout(t);
  }, [wait]);

  const backToPassword = (message = '') => {
    setStep(null);
    setCode('');
    setErrors({});
    setAlert(message);
  };

  const submitCode = async (e) => {
    e.preventDefault();
    if (!/^\d{6}$/.test(code)) {
      setErrors({ code: 'Enter the 6-digit code from the email.' });
      return;
    }
    setBusy(true);
    setAlert('');
    try {
      await verifySignIn(code);
      navigate(next, { replace: true });
    } catch (err) {
      if (err.errors?.restart) {
        backToPassword(err.message);
      } else {
        setErrors({ code: err.errors?.code?.[0] || err.message });
        setCode('');
        }
    } finally {
      setBusy(false);
    }
  };

  const resend = async () => {
    setBusy(true);
    setAlert('');
    try {
      const data = await resendSignIn();
      setWait(data.resend_in || 45);
      setStep((s) => ({ ...s, devCode: data.dev_code || '' }));
      setErrors({});
      setAlert('');
    } catch (err) {
      if (err.errors?.restart) backToPassword(err.message);
      else setAlert(err.message);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    if (!loading && user) navigate(next, { replace: true });
  }, [loading, user, navigate, next]);

  useEffect(() => {
    document.title = 'Sign in | Zentra Direct';
  }, []);

  const set = (k, v) => {
    setForm((f) => ({ ...f, [k]: v }));
    setErrors((e) => ({ ...e, [k]: undefined }));
  };

  const submit = async (e) => {
    e.preventDefault();
    const errs = {};
    if (!emailOk(form.email)) errs.email = 'Enter a valid email address.';
    if (!form.password) errs.password = 'Enter your password.';
    setErrors(errs);
    setAlert('');
    if (Object.keys(errs).length) {
      focusFirstError(formRef.current);
      return;
    }
    setBusy(true);
    try {
      const data = await signIn(form.email.trim(), form.password, form.remember);
      if (data.code_required) {
        setStep({ email: data.email, devCode: data.dev_code || '' });
        setWait(data.resend_in || 45);
        setCode('');
        setErrors({});
        setForm((f) => ({ ...f, password: '' }));
      } else {
        navigate(next, { replace: true });
      }
    } catch (err) {
      setAlert(err.message);
      setForm((f) => ({ ...f, password: '' }));
    } finally {
      setBusy(false);
    }
  };

  return (
    <main id="main" className="auth">
      <aside className="auth__aside">
        <Link to="/" className="auth__logo"><Logo light /></Link>
        <div className="auth__aside-copy">
          <h1>Welcome back</h1>
          <p>Sign in to trade, check your portfolio, or pick up your application where you left off.</p>
          <ul className="auth__points">
            <li><ShieldCheck size={20} aria-hidden="true" /> Your connection is encrypted</li>
            <li><Lock size={20} aria-hidden="true" /> We will never ask for your password by email or phone</li>
          </ul>
        </div>
      </aside>

      <section className="auth__main">
        <div className="auth__card">
          <Link to="/" className="auth__logo auth__logo--mobile"><Logo /></Link>
          {step ? (
            <>
              <h2>Check your email</h2>
              <p className="auth__sub">
                We sent a 6-digit sign-in code to <b>{step.email}</b>.
              </p>
              <FormAlert>{alert}</FormAlert>
              {step.devCode && (
                <p className="su-dev" role="note">Development mode: no email is sent. Your code is <b>{step.devCode}</b>.</p>
              )}
              <form onSubmit={submitCode} noValidate className="auth__form">
                <TextField
                  label="Sign-in code" name="code" value={code} error={errors.code}
                  onChange={(k, v) => { setCode(v.replace(/\D/g, '').slice(0, 6)); setErrors({}); }}
                  inputMode="numeric" autoComplete="one-time-code" maxLength={6} placeholder="123456"
                  className="auth__code" autoFocus required
                />
                <button type="submit" className="btn btn--primary btn--block" disabled={busy}>
                  {busy ? <><Loader2 size={18} className="spin" aria-hidden="true" /> Checking…</> : 'Verify and sign in'}
                </button>
              </form>
              <p className="auth__resend">
                Did not get it? Check your spam folder.{' '}
                <button type="button" className="text-btn" onClick={resend} disabled={busy || wait > 0}>
                  {wait > 0 ? `Send a new code in ${wait}s` : 'Send a new code'}
                </button>
              </p>
              <button type="button" className="text-btn auth__back" onClick={() => backToPassword()}>
                <ArrowLeft size={16} aria-hidden="true" /> Use a different account
              </button>
            </>
          ) : (
          <>
          <h2>Sign in</h2>
          <p className="auth__sub">
            New to Zentra Direct? <Link to="/sign-up">Open an account</Link>
          </p>
          <FormAlert>{alert}</FormAlert>
          <form ref={formRef} onSubmit={submit} noValidate className="auth__form">
            <TextField
              label="Email"
              name="email" maxLength={254}
              type="email"
              value={form.email}
              onChange={set}
              error={errors.email}
              autoComplete="username"
              inputMode="email"
              required
            />
            <PasswordField value={form.password} onChange={set} error={errors.password} />
            <div className="auth__row">
              <CheckboxField name="remember" checked={form.remember} onChange={set}>Keep me signed in</CheckboxField>
              <Link to="/forgot-password" state={{ email: form.email.trim() }} className="text-btn">
                Forgot password?
              </Link>
            </div>
            <button type="submit" className="btn btn--primary btn--block" disabled={busy}>
              {busy ? <><Loader2 size={18} className="spin" aria-hidden="true" /> Signing in…</> : 'Sign in'}
            </button>
          </form>
          </>
          )}
        </div>
      </section>
    </main>
  );
}
