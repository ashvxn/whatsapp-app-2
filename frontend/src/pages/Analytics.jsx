import { useEffect, useState } from "react";
import api from "../api";

// ── Icons ──────────────────────────────────────────────────────
const Ic = {
  Wallet:   () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 12V8H6a2 2 0 0 1-2-2c0-1.1.9-2 2-2h12v4"/><path d="M4 6v12c0 1.1.9 2 2 2h14v-4"/><path d="M18 12a2 2 0 0 0-2 2c0 1.1.9 2 2 2h4v-4h-4z"/></svg>,
  Send:     () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>,
  Eye:      () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>,
  Users:    () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>,
  Target:   () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>,
  Activity: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>,
  Refresh:  () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>,
  Zap:      () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>,
};

const CAT_COLORS  = { marketing: "#128c7e", service: "#0ea5e9", utility: "#f59e0b", other: "#94a3b8" };
const STATUS_META = {
  completed:  { color: "#16a34a", label: "Completed"  },
  partial:    { color: "#ea580c", label: "Partial"    },
  failed:     { color: "#dc2626", label: "Failed"     },
  scheduled:  { color: "#1d4ed8", label: "Scheduled"  },
  processing: { color: "#d97706", label: "Processing" },
};

// ── KPI Card ───────────────────────────────────────────────────
function KPICard({ icon, label, value, sub, color, bg }) {
  return (
    <div className="card" style={{ display: "flex", alignItems: "center", gap: "16px", padding: "20px 22px" }}>
      <div style={{ background: bg, color, padding: "10px", borderRadius: "10px", flexShrink: 0, display: "flex" }}>
        {icon}
      </div>
      <div style={{ minWidth: 0 }}>
        <div style={{ color: "var(--text-muted)", fontSize: "11px", fontWeight: "700", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "4px" }}>
          {label}
        </div>
        <div style={{ fontSize: "24px", fontWeight: "800", color: "var(--text-main)", lineHeight: 1.1 }}>{value}</div>
        {sub && <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "3px" }}>{sub}</div>}
      </div>
    </div>
  );
}

// ── SVG Donut Chart ────────────────────────────────────────────
function DonutChart({ segments, size = 160, thickness = 26 }) {
  const r     = (size - thickness) / 2;
  const cx    = size / 2;
  const cy    = size / 2;
  const circ  = 2 * Math.PI * r;
  const total = segments.reduce((s, seg) => s + seg.value, 0);

  let cumulative = 0;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: "rotate(-90deg)" }}>
      {total === 0 ? (
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#e2e8f0" strokeWidth={thickness} />
      ) : (
        segments.map((seg, i) => {
          const dash   = (seg.value / total) * circ;
          const offset = circ - (cumulative / total) * circ;
          cumulative  += seg.value;
          return (
            <circle
              key={i} cx={cx} cy={cy} r={r} fill="none"
              stroke={seg.color} strokeWidth={thickness}
              strokeDasharray={`${dash} ${circ}`}
              strokeDashoffset={offset}
              style={{ transition: "stroke-dasharray 0.8s ease" }}
            />
          );
        })
      )}
    </svg>
  );
}

// ── Funnel Stage ───────────────────────────────────────────────
function FunnelStage({ label, value, pct, color }) {
  return (
    <div style={{ marginBottom: "18px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: color }} />
          <span style={{ fontWeight: "600", fontSize: "13px" }}>{label}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontWeight: "700", fontSize: "15px" }}>{value.toLocaleString()}</span>
          <span style={{
            background: color + "20", color, fontSize: "10px", fontWeight: "700",
            padding: "2px 8px", borderRadius: "999px", minWidth: "40px", textAlign: "center"
          }}>{pct}%</span>
        </div>
      </div>
      <div style={{ height: "8px", background: "var(--bg-main)", borderRadius: "6px", overflow: "hidden" }}>
        <div style={{
          width: `${pct}%`, height: "100%", background: color, borderRadius: "6px",
          transition: "width 0.9s cubic-bezier(0.4,0,0.2,1)"
        }} />
      </div>
    </div>
  );
}

// ── Bar Trend Chart ────────────────────────────────────────────
function TrendChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)", fontSize: "14px" }}>
        No campaign data in the last 30 days
      </div>
    );
  }
  const maxSent = Math.max(...data.map(d => d.sent), 1);

  return (
    <div>
      <div style={{ display: "flex", gap: "16px", marginBottom: "16px" }}>
        {[{ color: "rgba(18,140,126,0.25)", label: "Sent" }, { color: "#128c7e", label: "Read" }].map(l => (
          <div key={l.label} style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px", color: "var(--text-muted)" }}>
            <div style={{ width: "12px", height: "10px", borderRadius: "2px", background: l.color }} />
            {l.label}
          </div>
        ))}
      </div>
      <div style={{ display: "flex", gap: "6px", alignItems: "flex-end", height: "130px", overflowX: "auto", paddingBottom: "28px" }}>
        {data.map((d, i) => (
          <div key={i} style={{ flex: "1", minWidth: "26px", display: "flex", flexDirection: "column", alignItems: "center", gap: "2px", height: "100%" }}>
            <div style={{ flex: 1, width: "100%", display: "flex", alignItems: "flex-end", gap: "2px" }}>
              <div
                title={`Sent: ${d.sent}`}
                style={{ flex: 1, background: "rgba(18,140,126,0.2)", borderRadius: "3px 3px 0 0", height: `${(d.sent / maxSent) * 100}%`, minHeight: d.sent > 0 ? "4px" : 0 }}
              />
              <div
                title={`Read: ${d.read}`}
                style={{ flex: 1, background: "#128c7e", borderRadius: "3px 3px 0 0", height: `${(d.read / maxSent) * 100}%`, minHeight: d.read > 0 ? "4px" : 0 }}
              />
            </div>
            <div style={{ fontSize: "9px", color: "var(--text-muted)", whiteSpace: "nowrap", transform: "rotate(-45deg)", transformOrigin: "top center", marginTop: "4px", width: "28px", textAlign: "center" }}>
              {d.date?.slice(5)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Read Rate Mini Bar ─────────────────────────────────────────
function RateBar({ pct }) {
  const color = pct >= 50 ? "#128c7e" : pct >= 25 ? "#f59e0b" : "#ef4444";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
      <div style={{ flex: 1, height: "5px", background: "var(--bg-main)", borderRadius: "3px", overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: "3px" }} />
      </div>
      <span style={{ fontSize: "11px", fontWeight: "700", color, minWidth: "30px" }}>{pct}%</span>
    </div>
  );
}

// ── Main ───────────────────────────────────────────────────────
export default function Analytics() {
  const [data, setData]               = useState(null);
  const [loading, setLoading]         = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [refreshing, setRefreshing]   = useState(false);

  const fetchData = (showSpinner = false) => {
    if (showSpinner) setRefreshing(true);
    api.get("/analytics/overview")
      .then(res => { setData(res.data); setLastUpdated(new Date()); })
      .catch(console.error)
      .finally(() => { setLoading(false); setRefreshing(false); });
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(() => fetchData(), 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", padding: "100px", color: "var(--text-muted)" }}>
      Loading analytics...
    </div>
  );
  if (!data) return <div className="card" style={{ textAlign: "center", padding: "40px" }}>No data available.</div>;

  const { kpis, campaign_status, breakdown, top_campaigns, daily_trend, funnel } = data;

  const donutSegments = Object.entries(breakdown).map(([cat, v]) => ({
    label: cat.charAt(0).toUpperCase() + cat.slice(1),
    value: v.spend,
    color: CAT_COLORS[cat] || "#94a3b8",
  }));
  const totalCatSpend = donutSegments.reduce((s, d) => s + d.value, 0);
  const statusTotal   = Object.values(campaign_status).reduce((s, v) => s + v, 0);
  const funnelPct     = (n) => funnel.sent > 0 ? Math.round(n / funnel.sent * 100) : 0;

  return (
    <div>
      {/* ── Header ── */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "28px" }}>
        <div>
          <h1 style={{ marginBottom: "4px" }}>Analytics</h1>
          <p style={{ color: "var(--text-muted)", fontSize: "14px", marginTop: 0 }}>
            Real-time WhatsApp campaign intelligence &amp; spend tracking
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          {lastUpdated && (
            <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
              Updated {lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
            </span>
          )}
          <button className="btn-outline" onClick={() => fetchData(true)} style={{ display: "flex", alignItems: "center", gap: "6px", padding: "6px 14px", fontSize: "13px" }}>
            <span style={{ display: "flex", animation: refreshing ? "spin 1s linear infinite" : "none" }}><Ic.Refresh /></span>
            Refresh
          </button>
        </div>
      </div>

      {/* ── KPI Row ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: "16px", marginBottom: "24px" }}>
        <KPICard icon={<Ic.Wallet />}   label="Total Spend"     value={"₹" + kpis.total_spend}              sub="Estimated cost to date"                      color="#128c7e" bg="rgba(18,140,126,0.1)" />
        <KPICard icon={<Ic.Activity />} label="Campaigns Run"   value={kpis.total_campaigns}                sub="Completed + partial"                         color="#8b5cf6" bg="rgba(139,92,246,0.1)" />
        <KPICard icon={<Ic.Send />}     label="Messages Sent"   value={kpis.total_sent.toLocaleString()}    sub={kpis.total_delivered.toLocaleString() + " delivered"} color="#0ea5e9" bg="rgba(14,165,233,0.1)" />
        <KPICard icon={<Ic.Eye />}      label="Read Rate"       value={kpis.read_rate + "%"}                sub={kpis.total_read.toLocaleString() + " reads"}  color="#f59e0b" bg="rgba(245,158,11,0.1)" />
        <KPICard icon={<Ic.Target />}   label="Delivery Rate"   value={kpis.delivery_rate + "%"}           sub="Sent → Delivered"                            color="#ec4899" bg="rgba(236,72,153,0.1)" />
        <KPICard icon={<Ic.Users />}    label="Active Contacts" value={kpis.active_contacts.toLocaleString()} sub="Opted in"                                 color="#64748b" bg="rgba(100,116,139,0.1)" />
      </div>

      {/* ── Funnel + Status ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: "20px", marginBottom: "20px" }}>
        <div className="card">
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "22px" }}>
            <span style={{ color: "var(--primary)" }}><Ic.Zap /></span>
            <h3 style={{ fontSize: "15px", fontWeight: "700", margin: 0 }}>Delivery Funnel</h3>
          </div>
          <FunnelStage label="Sent"      value={funnel.sent}      pct={100}                           color="#0ea5e9" />
          <FunnelStage label="Delivered" value={funnel.delivered} pct={funnelPct(funnel.delivered)}   color="#128c7e" />
          <FunnelStage label="Read"      value={funnel.read}      pct={funnelPct(funnel.read)}        color="#8b5cf6" />
          <div style={{ marginTop: "16px", padding: "10px 14px", background: "var(--bg-main)", borderRadius: "var(--radius)", fontSize: "13px", color: "var(--text-muted)", display: "flex", justifyContent: "space-between" }}>
            <span>Cost per read</span>
            <strong style={{ color: "var(--text-main)" }}>₹{kpis.cost_per_read}</strong>
          </div>
        </div>

        <div className="card">
          <h3 style={{ fontSize: "15px", fontWeight: "700", marginBottom: "20px" }}>Campaign Status</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {Object.entries(STATUS_META).map(([status, meta]) => {
              const count = campaign_status[status] || 0;
              const pct   = statusTotal > 0 ? Math.round(count / statusTotal * 100) : 0;
              return (
                <div key={status} style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <div style={{ width: "9px", height: "9px", borderRadius: "50%", background: meta.color, flexShrink: 0 }} />
                  <span style={{ flex: 1, fontSize: "13px" }}>{meta.label}</span>
                  <span style={{ fontWeight: "700", fontSize: "15px", minWidth: "28px", textAlign: "right" }}>{count}</span>
                  <div style={{ width: "72px", height: "5px", background: "var(--bg-main)", borderRadius: "3px", overflow: "hidden" }}>
                    <div style={{ width: `${pct}%`, height: "100%", background: meta.color, borderRadius: "3px" }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── Daily Trend ── */}
      <div className="card" style={{ marginBottom: "20px" }}>
        <h3 style={{ fontSize: "15px", fontWeight: "700", marginBottom: "16px" }}>
          Message Volume — Last 30 Days
        </h3>
        <TrendChart data={daily_trend} />
      </div>

      {/* ── Top Campaigns + Category Breakdown ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr", gap: "20px" }}>
        <div className="card">
          <h3 style={{ fontSize: "15px", fontWeight: "700", marginBottom: "16px" }}>Top Campaigns by Reach</h3>
          <div className="table-wrapper" style={{ maxHeight: "360px" }}>
            <table>
              <thead>
                <tr>
                  <th>Campaign</th>
                  <th style={{ textAlign: "center" }}>Sent</th>
                  <th style={{ textAlign: "center" }}>Delivered</th>
                  <th style={{ textAlign: "center" }}>Read</th>
                  <th style={{ minWidth: "110px" }}>Read Rate</th>
                  <th style={{ textAlign: "right" }}>Cost</th>
                </tr>
              </thead>
              <tbody>
                {top_campaigns.length === 0 ? (
                  <tr>
                    <td colSpan="6" style={{ textAlign: "center", padding: "32px", color: "var(--text-muted)" }}>No completed campaigns yet</td>
                  </tr>
                ) : (
                  top_campaigns.map(c => (
                    <tr key={c.id}>
                      <td>
                        <div style={{ fontWeight: "600", fontSize: "13px" }}>{c.name}</div>
                        <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                          #{c.id} · {c.date ? new Date(c.date).toLocaleDateString() : "—"}
                        </div>
                      </td>
                      <td style={{ textAlign: "center", fontWeight: "600" }}>{c.sent.toLocaleString()}</td>
                      <td style={{ textAlign: "center", fontWeight: "600", color: "#0ea5e9" }}>{c.delivered.toLocaleString()}</td>
                      <td style={{ textAlign: "center", fontWeight: "600", color: "var(--primary)" }}>{c.read.toLocaleString()}</td>
                      <td><RateBar pct={c.read_rate} /></td>
                      <td style={{ textAlign: "right", fontWeight: "700", fontSize: "13px" }}>₹{c.cost}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <h3 style={{ fontSize: "15px", fontWeight: "700", marginBottom: "20px" }}>Spend by Category</h3>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "20px" }}>
            <div style={{ position: "relative", display: "flex", justifyContent: "center" }}>
              <DonutChart segments={donutSegments} size={160} thickness={26} />
              <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", pointerEvents: "none" }}>
                <div style={{ fontSize: "17px", fontWeight: "800" }}>₹{totalCatSpend.toFixed(2)}</div>
                <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Total</div>
              </div>
            </div>
            <div style={{ width: "100%", display: "flex", flexDirection: "column", gap: "10px" }}>
              {donutSegments.length === 0 ? (
                <p style={{ color: "var(--text-muted)", textAlign: "center", fontSize: "13px" }}>No spend data</p>
              ) : (
                donutSegments.map((seg, i) => (
                  <div key={i}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                      <div style={{ width: "10px", height: "10px", borderRadius: "2px", background: seg.color, flexShrink: 0 }} />
                      <span style={{ flex: 1, fontSize: "13px", fontWeight: "500" }}>{seg.label}</span>
                      <span style={{ fontWeight: "700", fontSize: "13px" }}>₹{seg.value.toFixed(2)}</span>
                      <span style={{ fontSize: "11px", color: "var(--text-muted)", minWidth: "30px", textAlign: "right" }}>
                        {totalCatSpend > 0 ? Math.round(seg.value / totalCatSpend * 100) : 0}%
                      </span>
                    </div>
                    <div style={{ height: "3px", background: "var(--bg-main)", borderRadius: "2px", overflow: "hidden" }}>
                      <div style={{ width: `${totalCatSpend > 0 ? (seg.value / totalCatSpend) * 100 : 0}%`, height: "100%", background: seg.color, borderRadius: "2px" }} />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
