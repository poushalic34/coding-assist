import { useState } from "react";

export default function AuthPanel({ onSubmit, loading, error }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const submit = (event) => {
    event.preventDefault();
    if (!email.trim() || !password.trim()) {
      return;
    }
    onSubmit({ mode, email: email.trim(), password });
  };

  return (
    <div className="authShell">
      <form className="authPanel" onSubmit={submit}>
        <h1>{mode === "login" ? "Welcome back" : "Create account"}</h1>
        <p className="muted">
          {mode === "login"
            ? "Sign in to continue your practice."
            : "Create an account to save your progress."}
        </p>
        <label className="controlLabel">
          Email
          <input
            className="authInput"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@example.com"
            required
          />
        </label>
        <label className="controlLabel">
          Password
          <input
            className="authInput"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="At least 8 characters"
            minLength={8}
            required
          />
        </label>
        {error ? <p className="errorText">{error}</p> : null}
        <button className="primaryButton" type="submit" disabled={loading}>
          {loading ? "Please wait..." : mode === "login" ? "Login" : "Sign up"}
        </button>
        <button
          className="chipButton"
          type="button"
          onClick={() => setMode((prev) => (prev === "login" ? "signup" : "login"))}
        >
          {mode === "login" ? "Need an account? Sign up" : "Already have an account? Login"}
        </button>
      </form>
    </div>
  );
}
