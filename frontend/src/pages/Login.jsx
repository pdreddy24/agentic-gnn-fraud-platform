import { useState } from "react";
import { ShieldCheck } from "lucide-react";
import { postJson, saveUser, setToken } from "../api/client.js";

export default function Login({ onLoginSuccess }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const isLogin = mode === "login";

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const path = isLogin ? "/auth/login" : "/auth/signup";

      const result = await postJson(
        path,
        {
          email,
          password,
        },
        false
      );

      setToken(result.token);
      saveUser(result.user);
      onLoginSuccess(result.user);
    } catch (err) {
      setError(err.message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page-clean">
      <div className="auth-card-clean">
        <div className="auth-icon-clean">
          <ShieldCheck size={38} />
        </div>

        <h1>Fraud Detection Platform</h1>

        <p className="auth-subtitle">
          Login or create an account to upload transaction files.
        </p>

        <div className="auth-tab-row">
          <button
            type="button"
            className={isLogin ? "auth-tab active" : "auth-tab"}
            onClick={() => {
              setMode("login");
              setError("");
            }}
          >
            Login
          </button>

          <button
            type="button"
            className={!isLogin ? "auth-tab active" : "auth-tab"}
            onClick={() => {
              setMode("signup");
              setError("");
            }}
          >
            Sign Up
          </button>
        </div>

        <form className="auth-form-clean" onSubmit={handleSubmit}>
          <label>Email</label>
          <input
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            type="email"
            placeholder="Enter your email"
            required
          />

          <label>Password</label>
          <input
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            type="password"
            placeholder="Enter your password"
            minLength={6}
            required
          />

          {error && <div className="error-box">{error}</div>}

          <button className="auth-main-button" disabled={loading}>
            {loading ? "Please wait..." : isLogin ? "Login" : "Sign Up"}
          </button>
        </form>
      </div>
    </div>
  );
}