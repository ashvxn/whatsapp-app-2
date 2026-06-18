import { useEffect, useState } from "react";
import api from "../api";
import { Link } from "react-router-dom";

const Icons = {
  Search: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
  ),
  Filter: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon></svg>
  ),
  Plus: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
  ),
  ExternalLink: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
  ),
  Trash: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
  )
};

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const fetchCampaigns = () => {
    api.get("/campaigns")
      .then(res => {
        if (Array.isArray(res.data)) {
          setCampaigns(res.data);
          setError(null);
        } else {
          setError("Invalid data received.");
        }
      })
      .catch(err => {
        setError("Unable to reach backend.");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchCampaigns();
    const interval = setInterval(fetchCampaigns, 5000);
    return () => clearInterval(interval);
  }, []);

  const deleteCampaign = async (id) => {
    if (window.confirm("Delete this campaign record?")) {
      try {
        await api.delete(`/campaigns/${id}`);
        fetchCampaigns();
      } catch (err) {
        alert("Error deleting campaign.");
      }
    }
  };

  const filteredCampaigns = campaigns
    .filter(c => {
      const matchesSearch = c.template_name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === "all" || c.status === statusFilter;
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => b.id - a.id);

  if (error) {
    return (
      <div className="card" style={{ textAlign: "center", padding: "40px" }}>
        <h2 style={{ color: "var(--text-muted)" }}>⚠️ {error}</h2>
        <button className="btn-primary" onClick={fetchCampaigns}>Try Again</button>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center" style={{ marginBottom: "32px" }}>
        <div>
          <h1>Campaigns</h1>
          <p style={{ color: "var(--text-muted)", fontSize: "14px", marginTop: "4px" }}>Manage and monitor your WhatsApp broadcast campaigns.</p>
        </div>
        <Link to="/create-campaign">
          <button className="btn-primary"><Icons.Plus /> New Campaign</button>
        </Link>
      </div>

      <div className="card" style={{ padding: "16px" }}>
        <div className="flex items-center">
          <div style={{ position: "relative", flex: 1 }}>
            <span style={{ position: "absolute", left: "12px", top: "10px", color: "var(--text-muted)" }}><Icons.Search /></span>
            <input 
              type="text" 
              placeholder="Search campaigns..." 
              className="search-input"
              style={{ paddingLeft: "40px", marginBottom: 0, maxWidth: "100%" }}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ color: "var(--text-muted)", fontSize: "14px" }}><Icons.Filter /> Status:</span>
            <select 
              className="filter-select" 
              style={{ marginBottom: 0 }}
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all">All Statuses</option>
              <option value="scheduled">Scheduled</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="partial">Partial</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>
      </div>

      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Campaign</th>
              <th>Date</th>
              <th>Status</th>
              <th>Performance</th>
              <th style={{ textAlign: "right" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredCampaigns.length === 0 ? (
              <tr>
                <td colSpan="5" style={{ textAlign: "center", padding: "40px", color: "var(--text-muted)" }}>
                  {loading ? "Loading campaigns..." : "No campaigns found."}
                </td>
              </tr>
            ) : (
              filteredCampaigns.map(c => (
                <tr key={c.id}>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                      {c.payload?.image_url ? (
                        <img src={c.payload.image_url} alt="" style={{ width: "32px", height: "32px", objectFit: "cover", borderRadius: "4px" }} />
                      ) : (
                        <div style={{ width: "32px", height: "32px", background: "var(--bg-main)", borderRadius: "4px", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-muted)", fontSize: "10px" }}>IMG</div>
                      )}
                      <div style={{ fontWeight: "600" }}>{c.template_name}</div>
                    </div>
                  </td>
                  <td style={{ color: "var(--text-muted)", fontSize: "13px" }}>
                    {(() => {
                      const raw = c.created_at || c.scheduled_at;
                      if (!raw) return "—";
                      const d = new Date(raw);
                      if (isNaN(d)) return "—";
                      return (
                        <>
                          {d.toLocaleDateString()}
                          <div style={{ fontSize: "11px" }}>{d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                        </>
                      );
                    })()}
                  </td>
                  <td>
                    <span className={`badge badge-${c.status || 'unknown'}`}>{c.status}</span>
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: "12px", fontSize: "13px" }}>
                       <span title="Sent">Sent: <strong>{c.stats?.sent || 0}</strong></span>
                       <span title="Read" style={{ color: "var(--primary)" }}>Read: <strong>{c.stats?.read || 0}</strong></span>
                    </div>
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}>
                      <Link to={`/campaigns/${c.id}`}>
                        <button className="btn-outline" style={{ padding: "6px 10px" }} title="View Details">
                          <Icons.ExternalLink />
                        </button>
                      </Link>
                      <button 
                        className="btn-danger" 
                        style={{ padding: "6px 10px" }} 
                        title="Delete Record"
                        onClick={() => deleteCampaign(c.id)}
                      >
                        <Icons.Trash />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}