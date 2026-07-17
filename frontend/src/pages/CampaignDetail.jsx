import { useEffect, useState } from "react";
import api from "../api";
import { useParams, useNavigate, Link } from "react-router-dom";

const Icons = {
  ChevronLeft: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
  ),
  Check: () => (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
  ),
  CheckCircle: () => (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
  ),
  Retry: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
  )
};

function ReadReceipt({ status, style = {} }) {
  if (status === 'read')      return <span className="read-ticks read"      style={{ color: "#34b7f1", ...style }}><Icons.CheckCircle /><Icons.CheckCircle style={{marginLeft: "-8px"}} /></span>;
  if (status === 'delivered') return <span className="read-ticks delivered" style={{ color: "#94a3b8", ...style }}><Icons.CheckCircle /><Icons.CheckCircle style={{marginLeft: "-8px"}} /></span>;
  if (status === 'sent')      return <span className="read-ticks sent"      style={{ color: "#94a3b8", ...style }}><Icons.Check /></span>;
  return null;
}

export default function CampaignDetail() {
  const { id } = useParams();
  const [campaign, setCampaign] = useState(null);
  const [loading, setLoading] = useState(true);
  const [retrying, setRetrying] = useState(false);
  const [retryStatus, setRetryStatus] = useState(null);
  const navigate = useNavigate();

  const fetchDetails = () => {
    api.get(`/campaigns/${id}`)
      .then(res => setCampaign(res.data))
      .catch(err => {
        console.error(err);
        navigate("/campaigns");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchDetails();
    const interval = setInterval(fetchDetails, 5000);
    return () => clearInterval(interval);
  }, [id]);

  const retryFailed = async () => {
    setRetrying(true);
    setRetryStatus(null);
    try {
      const res = await api.post(`/campaigns/${id}/retry`);
      const { sent, failed } = res.data;
      setRetryStatus(`Retry complete: ${sent} sent, ${failed} still failed.`);
      await fetchDetails();
    } catch (err) {
      setRetryStatus(err.response?.data?.message || "Error retrying failed sends.");
    } finally {
      setRetrying(false);
    }
  };

  if (loading && !campaign) return <div style={{ display: "flex", justifyContent: "center", padding: "100px" }}><p>Loading campaign details...</p></div>;
  if (!campaign) return null;

  const recipients = campaign.recipients || [];
  const payload = campaign.payload || {};
  const stats = {
    sent: recipients.filter(r => r.status !== 'failed').length,
    delivered: recipients.filter(r => r.status === 'delivered' || r.status === 'read').length,
    read: recipients.filter(r => r.status === 'read').length,
    failed: recipients.filter(r => r.status === 'failed').length
  };

  const isTemplate = !["CUSTOM_TEXT", "CUSTOM_IMAGE"].includes(campaign.template_name);

  return (
    <div>
      <div style={{ marginBottom: "24px" }}>
        <Link to="/campaigns" style={{ display: "flex", alignItems: "center", gap: "4px", color: "var(--text-muted)", fontSize: "14px", fontWeight: "500" }}>
          <Icons.ChevronLeft /> Back to Campaigns
        </Link>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "32px" }}>
        <div>
          <h1 style={{ marginBottom: "4px" }}>{isTemplate ? "Template Campaign" : "Custom Campaign"}</h1>
          <p style={{ color: "var(--text-muted)", fontSize: "14px" }}>
            Campaign ID: <strong>#{campaign.id}</strong> • Template: <strong>{campaign.template_name}</strong>
          </p>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "6px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            {stats.failed > 0 && (
              <button className="btn-outline" style={{ display: "flex", alignItems: "center", gap: "6px" }} onClick={retryFailed} disabled={retrying}>
                <Icons.Retry /> {retrying ? "Retrying..." : `Retry Failed (${stats.failed})`}
              </button>
            )}
            <span className={`badge badge-${campaign.status || 'unknown'}`} style={{ padding: "6px 16px", fontSize: "12px" }}>
              {campaign.status}
            </span>
          </div>
          {retryStatus && (
            <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>{retryStatus}</div>
          )}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.5fr", gap: "32px" }}>
        <div className="flex-col" style={{ gap: "32px" }}>
          <div className="card">
            <h3 style={{ fontSize: "16px", marginBottom: "20px" }}>Preview</h3>
            <div style={{
                background: "#efe7de",
                padding: "20px",
                borderRadius: "12px",
                position: "relative",
                backgroundImage: "url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png')",
                backgroundSize: "contain"
            }}>
                <div style={{
                    background: "white",
                    padding: "6px",
                    borderRadius: "8px",
                    boxShadow: "0 1px 0.5px rgba(0,0,0,0.13)",
                    maxWidth: "90%"
                }}>
                    {payload.image_url && (
                        <img
                            src={payload.image_url}
                            alt=""
                            style={{ width: "100%", borderRadius: "6px", marginBottom: "4px", display: "block" }}
                        />
                    )}
                    <div style={{ padding: "4px 8px 0", fontSize: "14px", whiteSpace: "pre-wrap", color: "#111" }}>
                        {isTemplate && (
                            <div style={{ color: "var(--primary)", fontWeight: "700", fontSize: "11px", marginBottom: "2px", textTransform: "uppercase" }}>
                                {campaign.template_name}
                            </div>
                        )}
                        {payload.message || (Array.isArray(payload.variables) ? payload.variables.filter(Boolean).join("\n\n") : "") || "(No message content)"}
                    </div>
                    <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "center", gap: "4px", padding: "0 4px 4px", fontSize: "10px", color: "#667781" }}>
                        <span>{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        <ReadReceipt status={stats.read > 0 ? 'read' : stats.delivered > 0 ? 'delivered' : 'sent'} />
                    </div>
                </div>
            </div>
          </div>

          <div className="card">
            <h3 style={{ fontSize: "16px", marginBottom: "20px" }}>Performance Metrics</h3>
            <div style={{ display: "grid", gridTemplateColumns: stats.failed > 0 ? "1fr 1fr 1fr 1fr" : "1fr 1fr 1fr", gap: "16px" }}>
                <div style={{ textAlign: "center", padding: "16px", background: "var(--bg-main)", borderRadius: "var(--radius)" }}>
                    <div style={{ fontSize: "20px", fontWeight: "700" }}>{stats.sent}</div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", marginTop: "4px" }}>Sent</div>
                </div>
                <div style={{ textAlign: "center", padding: "16px", background: "var(--bg-main)", borderRadius: "var(--radius)" }}>
                    <div style={{ fontSize: "20px", fontWeight: "700", color: "var(--secondary)" }}>{stats.delivered}</div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", marginTop: "4px" }}>Delivered</div>
                </div>
                <div style={{ textAlign: "center", padding: "16px", background: "var(--bg-main)", borderRadius: "var(--radius)" }}>
                    <div style={{ fontSize: "20px", fontWeight: "700", color: "var(--primary)" }}>{stats.read}</div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", marginTop: "4px" }}>Read</div>
                </div>
                {stats.failed > 0 && (
                  <div style={{ textAlign: "center", padding: "16px", background: "var(--bg-main)", borderRadius: "var(--radius)" }}>
                      <div style={{ fontSize: "20px", fontWeight: "700", color: "#991b1b" }}>{stats.failed}</div>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", marginTop: "4px" }}>Failed</div>
                  </div>
                )}
            </div>
          </div>
        </div>

        <div className="card" style={{ display: "flex", flexDirection: "column" }}>
          <h3 style={{ fontSize: "16px", marginBottom: "20px" }}>Recipient Delivery Status</h3>
          <div className="table-wrapper" style={{ flex: 1, maxHeight: "600px" }}>
            <table style={{ border: "none" }}>
              <thead style={{ position: "sticky", top: 0, zIndex: 1 }}>
                <tr>
                  <th style={{ background: "var(--white)" }}>Contact</th>
                  <th style={{ background: "var(--white)" }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {recipients.map((r, i) => (
                  <tr key={i}>
                    <td>
                      <div style={{ fontWeight: "600" }}>{r.contact_name}</div>
                      <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>{r.phone}</div>
                    </td>
                    <td>
                       <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span className={`badge badge-${r.status}`} style={{ fontSize: "10px" }}>
                          {r.status}
                        </span>
                        <ReadReceipt status={r.status} />
                       </div>
                    </td>
                  </tr>
                ))}
                {recipients.length === 0 && (
                  <tr><td colSpan="2" style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)" }}>Initializing delivery...</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}