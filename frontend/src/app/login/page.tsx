"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";

import { auth } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

export default function LoginPage() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const setTokens = useAuthStore((s) => s.setTokens);
  const setUser = useAuthStore((s) => s.setUser);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // If already logged in, bounce to dashboard.
  useEffect(() => {
    if (accessToken) router.replace("/dashboard");
  }, [accessToken, router]);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const tokens = await auth.login(email, password);
      setTokens(tokens.access_token, tokens.refresh_token);
      // Fetch the user record so the header can show the name and we can role-gate.
      const me = await auth.me();
      setUser(me);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="qp-login-shell">
      <div className="qp-login-card">
        <h1>Sign in</h1>
        <p style={{ color: "var(--color-muted)", marginTop: 0 }}>
          Quran Student Progress Tracking
        </p>
        <form onSubmit={handleSubmit} className="qp-form">
          <div>
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error ? <div className="qp-error">{error}</div> : null}
          <button type="submit" className="qp-btn" disabled={submitting}>
            {submitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
        <p style={{ marginTop: 16, fontSize: "0.8rem", color: "var(--color-muted)" }}>
          Demo seed creates <code>teacher@example.com</code> /{" "}
          <code>teacher123!</code> and <code>admin@example.com</code> /{" "}
          <code>admin123!</code>.
        </p>
      </div>
    </div>
  );
}
