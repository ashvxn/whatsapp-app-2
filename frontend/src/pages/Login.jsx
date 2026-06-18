import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.post("/login", { username, password });
      localStorage.setItem("amd_token", res.data.token);
      navigate("/");
    } catch (err) {
      setError("Invalid username or password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg-main)" }}>
      <div className="card" style={{ width: "360px", padding: "32px" }}>
        <div style={{ textAlign: "center", marginBottom: "28px" }}>
          <img src="/amd-logo.jpeg" alt="AMD" style={{ width: "56px", height: "56px", borderRadius: "10px", objectFit: "cover", marginBottom: "10px" }} />
          <div style={{ fontSize: "22px", fontWeight: "bold" }}>AMD</div>
          <div style={{ color: "var(--text-muted)", fontSize: "13px", marginTop: "2px" }}>Academy of Media and Design</div>
        </div>
        <form onSubmit={submit}>
          <label style={{ display: "block", marginBottom: "8px", fontWeight: "600", fontSize: "14px" }}>Username</label>
          <input
            value={username}
            onChange={e => setUsername(e.target.value)}
            required
            autoFocus
            style={{ marginBottom: "16px" }}
          />
          <label style={{ display: "block", marginBottom: "8px", fontWeight: "600", fontSize: "14px" }}>Password</label>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            style={{ marginBottom: "16px" }}
          />
          {error && (
            <div style={{ color: "#dc2626", fontSize: "13px", marginBottom: "12px" }}>{error}</div>
          )}
          <button type="submit" className="btn-primary" style={{ width: "100%" }} disabled={loading}>
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
        <div style={{ textAlign: "center", marginTop: "20px", fontSize: "11px" }}>
          <a
            href="https://obsidyne.com"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: "var(--text-muted)", opacity: 0.6, textDecoration: "none" }}
          >
            Powered by Obsidyne
          </a>
        </div>
      </div>
    </div>
  );
}
