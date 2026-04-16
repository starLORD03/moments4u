"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const { login, register } = useAuth();
  const router = useRouter();

  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("parent");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (isRegister) {
        await register({ email, password, full_name: fullName, role });
      } else {
        await login(email, password);
      }
      router.push("/");
    } catch (err: any) {
      setError(err.detail || err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background:
          "linear-gradient(135deg, #fff7ed 0%, #faf5ff 50%, #f0f9ff 100%)",
        padding: "var(--space-md)",
      }}
    >
      <div className="card card-elevated slide-up" style={{ maxWidth: 420, width: "100%" }}>
        {/* Logo / Brand */}
        <div className="text-center" style={{ marginBottom: "var(--space-xl)" }}>
          <div
            style={{
              fontSize: "2.5rem",
              marginBottom: "var(--space-sm)",
            }}
          >
            📸
          </div>
          <h1
            className="font-display"
            style={{
              fontSize: "1.75rem",
              fontWeight: 800,
              background:
                "linear-gradient(135deg, var(--color-primary-500), var(--color-accent-500))",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            moments4u
          </h1>
          <p className="text-secondary text-sm" style={{ marginTop: 4 }}>
            {isRegister
              ? "Create your account"
              : "Capture & share learning moments"}
          </p>
        </div>

        {/* Error */}
        {error && (
          <div
            style={{
              background: "rgba(239, 68, 68, 0.08)",
              color: "var(--color-danger-500)",
              padding: "var(--space-sm) var(--space-md)",
              borderRadius: "var(--border-radius-md)",
              fontSize: "0.875rem",
              marginBottom: "var(--space-md)",
            }}
          >
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "var(--space-md)" }}>
          {isRegister && (
            <div>
              <label className="label" htmlFor="fullName">Full Name</label>
              <input
                id="fullName"
                className="input"
                type="text"
                placeholder="Sarah Johnson"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            </div>
          )}

          <div>
            <label className="label" htmlFor="email">Email</label>
            <input
              id="email"
              className="input"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>

          <div>
            <label className="label" htmlFor="password">Password</label>
            <input
              id="password"
              className="input"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              autoComplete={isRegister ? "new-password" : "current-password"}
            />
          </div>

          {isRegister && (
            <div>
              <label className="label" htmlFor="role">I am a...</label>
              <select
                id="role"
                className="input"
                value={role}
                onChange={(e) => setRole(e.target.value)}
              >
                <option value="parent">👨‍👩‍👧 Parent</option>
                <option value="teacher">🧑‍🏫 Teacher / Caregiver</option>
              </select>
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary btn-lg"
            disabled={loading}
            style={{ width: "100%", marginTop: "var(--space-sm)" }}
          >
            {loading ? (
              <span className="spinner" style={{ width: 20, height: 20, borderWidth: 2 }} />
            ) : isRegister ? (
              "Create Account"
            ) : (
              "Sign In"
            )}
          </button>
        </form>

        {/* Toggle */}
        <p
          className="text-center text-sm text-secondary"
          style={{ marginTop: "var(--space-lg)" }}
        >
          {isRegister ? "Already have an account?" : "Don't have an account?"}{" "}
          <button
            onClick={() => {
              setIsRegister(!isRegister);
              setError("");
            }}
            style={{
              color: "var(--color-primary-500)",
              fontWeight: 600,
              background: "none",
              border: "none",
              cursor: "pointer",
            }}
          >
            {isRegister ? "Sign In" : "Sign Up"}
          </button>
        </p>
      </div>
    </div>
  );
}
