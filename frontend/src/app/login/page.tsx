"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";

import { LangSwitcher } from "@/components/LangSwitcher";
import { auth } from "@/lib/api";
import { useT } from "@/lib/useT";
import { useAuthStore } from "@/store/auth";

export default function LoginPage() {
  const router = useRouter();
  const t = useT();
  const accessToken = useAuthStore((s) => s.accessToken);
  const setTokens = useAuthStore((s) => s.setTokens);
  const setUser = useAuthStore((s) => s.setUser);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

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
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
          }}
        >
          <div>
            <h1>{t("auth.signIn")}</h1>
            <p style={{ color: "var(--color-muted)", marginTop: 0 }}>
              {t("app.title")}
            </p>
          </div>
          <LangSwitcher />
        </div>
        <form onSubmit={handleSubmit} className="qp-form">
          <div>
            <label htmlFor="email">{t("auth.email")}</label>
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
            <label htmlFor="password">{t("auth.password")}</label>
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
            {submitting ? t("auth.signingIn") : t("auth.signIn")}
          </button>
        </form>
        <p style={{ marginTop: 16, fontSize: "0.8rem", color: "var(--color-muted)" }}>
          {t("auth.demoHint")}
        </p>
      </div>
    </div>
  );
}
