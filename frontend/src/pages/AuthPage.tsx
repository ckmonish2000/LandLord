import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth";
import { HomeIcon } from "../components/Icons";

export default function AuthPage({ mode }: { mode: "login" | "signup" }) {
  const { login, signup } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const isSignup = mode === "signup";

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (isSignup) await signup(name.trim(), email.trim(), password);
      else await login(email.trim(), password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <form className="auth-card" onSubmit={onSubmit}>
        <div className="auth-brand">
          <span className="auth-logo"><HomeIcon size={26} /></span>
          <span>Landlord</span>
        </div>
        <h1>{isSignup ? "Create your account" : "Welcome back"}</h1>
        <p className="muted">
          {isSignup ? "Sign up to link your WhatsApp and manage your groups." : "Sign in to see your WhatsApp groups."}
        </p>

        {isSignup && (
          <label className="field">
            <span>Name</span>
            <input value={name} onChange={(e) => setName(e.target.value)} required autoComplete="name" />
          </label>
        )}
        <label className="field">
          <span>Email</span>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
        </label>
        <label className="field">
          <span>Password</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={isSignup ? 8 : undefined}
            autoComplete={isSignup ? "new-password" : "current-password"}
          />
          {isSignup && <small className="muted">At least 8 characters</small>}
        </label>

        {error && <div className="form-error" role="alert">{error}</div>}

        <button className="btn-primary" type="submit" disabled={busy}>
          {busy ? "Please wait…" : isSignup ? "Sign up" : "Log in"}
        </button>

        <p className="auth-switch muted">
          {isSignup ? "Already have an account? " : "New here? "}
          <Link to={isSignup ? "/login" : "/signup"}>{isSignup ? "Log in" : "Create an account"}</Link>
        </p>
      </form>
    </main>
  );
}
