import { useState } from "react";
import api from "../api";
import { useNavigate, Link } from "react-router-dom";

const Icons = {
  ChevronLeft: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
  ),
  User: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
  )
};

export default function CreateContact() {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [tags, setTags] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/contacts", { name, phone, tags });
      navigate("/");
    } catch (err) {
      alert("Error adding contact. Make sure the backend is running and CORS is enabled.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: "600px", margin: "0 auto" }}>
      <div style={{ marginBottom: "24px" }}>
        <Link to="/" style={{ display: "flex", alignItems: "center", gap: "4px", color: "var(--text-muted)", fontSize: "14px", fontWeight: "500" }}>
          <Icons.ChevronLeft /> Back to Leads
        </Link>
      </div>

      <div style={{ marginBottom: "32px" }}>
        <h1>Add New Contact</h1>
        <p style={{ color: "var(--text-muted)", fontSize: "14px", marginTop: "4px" }}>Manually add a new lead to your database.</p>
      </div>

      <div className="card">
        <form onSubmit={submit}>
          <div style={{ marginBottom: "20px" }}>
            <label style={{ display: "block", marginBottom: "8px", fontWeight: "600", fontSize: "14px" }}>Full Name</label>
            <input
              placeholder="e.g. John Doe"
              value={name}
              onChange={e => setName(e.target.value)}
              required
              style={{ marginBottom: 0 }}
            />
          </div>

          <div style={{ marginBottom: "20px" }}>
            <label style={{ display: "block", marginBottom: "8px", fontWeight: "600", fontSize: "14px" }}>Phone Number</label>
            <input
              placeholder="e.g. 919876543210 (with country code)"
              value={phone}
              onChange={e => setPhone(e.target.value)}
              required
              style={{ marginBottom: 0 }}
            />
          </div>

          <div style={{ marginBottom: "24px" }}>
            <label style={{ display: "block", marginBottom: "8px", fontWeight: "600", fontSize: "14px" }}>Tags (comma separated)</label>
            <input
              placeholder="e.g. customer, student, vip"
              value={tags}
              onChange={e => setTags(e.target.value)}
              style={{ marginBottom: 0 }}
            />
            <p style={{ color: "var(--text-muted)", fontSize: "12px", marginTop: "4px" }}>Tags help you segment your contacts for targeted campaigns.</p>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px" }}>
            <Link to="/">
              <button type="button" className="btn-outline">Cancel</button>
            </Link>
            <button type="submit" className="btn-primary" style={{ minWidth: "140px" }} disabled={loading}>
              {loading ? "Adding..." : "Save Contact"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}