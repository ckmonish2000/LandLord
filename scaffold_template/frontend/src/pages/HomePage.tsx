import { useAuth } from "../auth";
import { LogoutIcon } from "../components/Icons";

/** Signed in landing page. Replace with the app's first real screen. */
export default function HomePage() {
  const { user, logout } = useAuth();
  if (!user) return null;

  return (
    <main className="home">
      <section className="home-card">
        <h1>Hi {user.name}</h1>
        <p className="muted">You're signed in. Build the first screen of __PROJECT_NAME__ here.</p>
        <div className="home-row">
          <span className="muted">Email</span>
          <span>{user.email}</span>
        </div>
        <div className="home-row">
          <span className="muted">Member since</span>
          <span>{new Date(user.created_at).toLocaleDateString()}</span>
        </div>
        <button className="btn btn-secondary" onClick={logout}>
          <LogoutIcon size={18} />
          Log out
        </button>
      </section>
    </main>
  );
}
