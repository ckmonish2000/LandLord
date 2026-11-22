import type { ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth";
import AuthPage from "./pages/AuthPage";
import HomePage from "./pages/HomePage";

function Splash() {
  return <div className="splash">Loading…</div>;
}

function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <Splash />;
  return user ? children : <Navigate to="/login" replace />;
}

function GuestOnly({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <Splash />;
  return user ? <Navigate to="/" replace /> : children;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<GuestOnly><AuthPage mode="login" /></GuestOnly>} />
          <Route path="/signup" element={<GuestOnly><AuthPage mode="signup" /></GuestOnly>} />
          <Route path="/" element={<RequireAuth><HomePage /></RequireAuth>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
