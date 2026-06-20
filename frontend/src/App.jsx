import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import api from "./api";
import Contacts from "./pages/Contacts";
import CreateContact from "./pages/CreateContact";
import Campaigns from "./pages/Campaigns";
import CreateCampaign from "./pages/CreateCampaign";
import CampaignDetail from "./pages/CampaignDetail";
import Analytics from "./pages/Analytics";
import Gallery from "./pages/Gallery";
import Login from "./pages/Login";

const Icons = {
  Contacts: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
  ),
  AddContact: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="17" y1="11" x2="23" y2="11"></line></svg>
  ),
  Campaigns: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
  ),
  CreateCampaign: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line></svg>
  ),
  Analytics: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
  ),
  Gallery: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
  ),
  Logout: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
  )
};

const QUALITY_COLORS = { GREEN: "#22c55e", YELLOW: "#eab308", RED: "#ef4444" };
const TIER_LABELS = {
  TIER_50: "50/day", TIER_250: "250/day", TIER_1K: "1K/day",
  TIER_10K: "10K/day", TIER_100K: "100K/day", TIER_UNLIMITED: "Unlimited"
};

function NumberStatus() {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    const fetchStatus = () => {
      api.get("/analytics/number-status")
        .then(res => { if (active) { setStatus(res.data); setError(false); } })
        .catch(() => { if (active) setError(true); });
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 60000);
    return () => { active = false; clearInterval(interval); };
  }, []);

  const color = status && !error ? (QUALITY_COLORS[status.quality_rating] || "#94a3b8") : "#475569";

  return (
    <div style={{ padding: "10px 24px", display: "flex", alignItems: "center", gap: "8px", fontSize: "12px", color: "var(--text-sidebar)", borderBottom: "1px solid rgba(255,255,255,0.05)", marginBottom: "20px" }}>
      <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: color, flexShrink: 0 }} />
      {error ? (
        <span style={{ opacity: 0.6 }}>Number status unavailable</span>
      ) : status ? (
        <span>Quality: <strong>{status.quality_rating || "Unknown"}</strong> · {TIER_LABELS[status.messaging_limit_tier] || status.messaging_limit_tier || "—"}</span>
      ) : (
        <span style={{ opacity: 0.6 }}>Checking number status…</span>
      )}
    </div>
  );
}

function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const isActive = (path) => location.pathname === path || (path === "/campaigns" && location.pathname.startsWith("/campaigns/"));

  const navItemStyle = (path) => ({
    display: "flex",
    alignItems: "center",
    gap: "12px",
    padding: "12px 20px",
    borderRadius: "var(--radius)",
    background: isActive(path) ? "var(--sidebar-active)" : "transparent",
    color: isActive(path) ? "var(--white)" : "var(--text-sidebar)",
    fontWeight: "500",
    transition: "all 0.2s ease",
    marginBottom: "4px",
    fontSize: "14px"
  });

  const logout = () => {
    localStorage.removeItem("amd_token");
    navigate("/login");
  };

  return (
    <div className="sidebar" style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ padding: "24px 24px 20px", color: "var(--white)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <img src="/amd-logo.jpeg" alt="AMD" style={{ width: "32px", height: "32px", borderRadius: "6px", objectFit: "cover" }} />
          <div>
            <div style={{ fontSize: "18px", fontWeight: "bold", letterSpacing: "0.5px", lineHeight: 1.1 }}>AMD</div>
            <div style={{ fontSize: "11px", opacity: 0.7 }}>Academy of Media and Design</div>
          </div>
        </div>
      </div>
      <NumberStatus />
      <div style={{ padding: "0 12px", flex: 1 }}>
        <Link to="/" style={navItemStyle("/")}>
          <Icons.Contacts /> Contacts
        </Link>
        <Link to="/add-contact" style={navItemStyle("/add-contact")}>
          <Icons.AddContact /> Add Contact
        </Link>
        <Link to="/campaigns" style={navItemStyle("/campaigns")}>
          <Icons.Campaigns /> Campaigns
        </Link>
        <Link to="/create-campaign" style={navItemStyle("/create-campaign")}>
          <Icons.CreateCampaign /> New Campaign
        </Link>
        <Link to="/analytics" style={navItemStyle("/analytics")}>
          <Icons.Analytics /> Analytics
        </Link>
        <Link to="/gallery" style={navItemStyle("/gallery")}>
          <Icons.Gallery /> Gallery
        </Link>
      </div>
      <div style={{ padding: "12px" }}>
        <button
          onClick={logout}
          style={{ ...navItemStyle("__logout__"), width: "100%", border: "none", background: "transparent", cursor: "pointer" }}
        >
          <Icons.Logout /> Logout
        </button>
      </div>
      <div style={{ padding: "12px 20px 18px", fontSize: "11px", textAlign: "center" }}>
        <a
          href="https://obsidyne.com"
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: "var(--text-sidebar)", opacity: 0.5, textDecoration: "none" }}
        >
          Powered by Obsidyne
        </a>
      </div>
    </div>
  );
}

function ProtectedLayout({ children }) {
  const token = localStorage.getItem("amd_token");
  if (!token) return <Navigate to="/login" replace />;
  return (
    <div className="layout-wrapper">
      <Sidebar />
      <main className="main-content">
        <div className="container">{children}</div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<ProtectedLayout><Contacts /></ProtectedLayout>} />
        <Route path="/add-contact" element={<ProtectedLayout><CreateContact /></ProtectedLayout>} />
        <Route path="/campaigns" element={<ProtectedLayout><Campaigns /></ProtectedLayout>} />
        <Route path="/campaigns/:id" element={<ProtectedLayout><CampaignDetail /></ProtectedLayout>} />
        <Route path="/create-campaign" element={<ProtectedLayout><CreateCampaign /></ProtectedLayout>} />
        <Route path="/analytics" element={<ProtectedLayout><Analytics /></ProtectedLayout>} />
        <Route path="/gallery" element={<ProtectedLayout><Gallery /></ProtectedLayout>} />
      </Routes>
    </BrowserRouter>
  );
}