import { useEffect, useState, useMemo } from "react";
import api from "../api";
import { Link, useNavigate } from "react-router-dom";
import Modal from "../components/Modal";

const Icons = {
  Search: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
  ),
  Phone: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l2.27-2.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
  ),
  Trash: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
  ),
  Plus: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
  ),
  Chevron: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
  ),
};

const TAG_STYLES = {
  interested:        { background: "#dcfce7", color: "#166534" },
  course:            { background: "#dbeafe", color: "#1e40af" },
  "course 1":        { background: "#e0e7ff", color: "#3730a3" },
  lead:              { background: "#fef9c3", color: "#854d0e" },
  not_interested:    { background: "#f1f5f9", color: "#64748b" },
  "verified lead":   { background: "#ede9fe", color: "#5b21b6" },
  "details captured":{ background: "#cffafe", color: "#0e7490" },
  "id available":    { background: "#fce7f3", color: "#9d174d" },
};

// Tags that open a popup instead of filtering the list when clicked.
const POPUP_TAGS = new Set(["details captured", "id available"]);

const GROUP_ORDER = ["interested", "lead", "course", "course 1", "not_interested"];

function getTagStyle(tag) {
  return TAG_STYLES[tag.trim().toLowerCase()] || { background: "var(--bg-main)", color: "var(--text-muted)" };
}

export default function Contacts() {
  const navigate = useNavigate();
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [activeGroup, setActiveGroup] = useState("All");
  const [expandedCombos, setExpandedCombos] = useState(new Set());
  const [visibleCount, setVisibleCount] = useState(12);
  const [detailsModal, setDetailsModal] = useState(null); // { contact, data, error }
  const [idProofModal, setIdProofModal] = useState(null); // { contact, imageUrl, error }

  useEffect(() => { setVisibleCount(12); }, [activeGroup, searchTerm]);

  const toggleCombo = (key) => {
    setExpandedCombos(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  };

  const fetchContacts = () => {
    setLoading(true);
    api.get("/contacts")
      .then(res => {
        if (Array.isArray(res.data)) {
          setContacts(res.data);
          setError(null);
        } else {
          setError("Invalid data received.");
        }
      })
      .catch(() => setError("Unable to reach backend."))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchContacts(); }, []);

  const deleteContact = async (id) => {
    if (window.confirm("Are you sure?")) {
      await api.delete(`/contacts/${id}`);
      fetchContacts();
    }
  };

  const openDetailsModal = async (contact) => {
    setDetailsModal({ contact, data: null, error: null });
    try {
      const res = await api.get(`/contacts/${contact.id}/scholarship`);
      setDetailsModal({ contact, data: res.data, error: null });
    } catch {
      setDetailsModal({ contact, data: null, error: "Unable to load details." });
    }
  };

  const openIdProofModal = async (contact) => {
    setIdProofModal({ contact, imageUrl: null, error: null });
    try {
      const res = await api.get(`/contacts/${contact.id}/id-proof`, { responseType: "blob" });
      const url = URL.createObjectURL(res.data);
      setIdProofModal({ contact, imageUrl: url, error: null });
    } catch {
      setIdProofModal({ contact, imageUrl: null, error: "Unable to load ID proof." });
    }
  };

  const closeIdProofModal = () => {
    if (idProofModal?.imageUrl) URL.revokeObjectURL(idProofModal.imageUrl);
    setIdProofModal(null);
  };

  const handleTagClick = (tag, contact) => {
    const norm = tag.trim().toLowerCase();
    if (norm === "details captured") openDetailsModal(contact);
    else if (norm === "id available") openIdProofModal(contact);
    else setActiveGroup(norm);
  };

  // Build label groups, normalized case-insensitively: { normalizedTag: { label, count } }
  // "lead", "LEAD", "Lead" all collapse into a single group.
  const labelGroups = useMemo(() => {
    const tagMap = {};
    contacts.forEach(c => {
      if (c.tags) {
        c.tags.split(",").forEach(t => {
          const trimmed = t.trim();
          if (!trimmed) return;
          const key = trimmed.toLowerCase();
          if (!tagMap[key]) tagMap[key] = { label: trimmed, count: 0 };
          tagMap[key].count += 1;
        });
      }
    });
    // Sort by predefined order first, then by count
    const entries = Object.entries(tagMap);
    entries.sort((a, b) => {
      const ai = GROUP_ORDER.indexOf(a[0]);
      const bi = GROUP_ORDER.indexOf(b[0]);
      if (ai !== -1 && bi !== -1) return ai - bi;
      if (ai !== -1) return -1;
      if (bi !== -1) return 1;
      return b[1].count - a[1].count;
    });
    return entries; // [normalizedKey, { label, count }]
  }, [contacts]);

  const filteredContacts = useMemo(() => {
    let result = contacts;
    if (activeGroup !== "All") {
      result = result.filter(c =>
        c.tags && c.tags.split(",").map(t => t.trim().toLowerCase()).includes(activeGroup)
      );
    }
    if (searchTerm) {
      result = result.filter(c =>
        c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.phone.includes(searchTerm)
      );
    }
    return result;
  }, [contacts, activeGroup, searchTerm]);

  // Group contacts by their exact combination of labels (case/whitespace-insensitive).
  // e.g. "lead, course1" and "Lead, Course1" merge into one group; "lead, course2" is separate.
  const comboGroups = useMemo(() => {
    const map = {};
    contacts.forEach(c => {
      const rawTags = c.tags ? c.tags.split(",").map(t => t.trim()).filter(Boolean) : [];
      const seen = new Map(); // normalized -> display casing (first seen)
      rawTags.forEach(t => {
        const norm = t.toLowerCase();
        if (!seen.has(norm)) seen.set(norm, t);
      });
      const normSorted = Array.from(seen.keys()).sort();
      const key = normSorted.length ? normSorted.join("|") : "__no_label__";
      if (!map[key]) {
        const label = normSorted.length
          ? normSorted.map(n => seen.get(n)).join(", ")
          : "No Label";
        map[key] = { key, label, tags: normSorted, contacts: [] };
      }
      map[key].contacts.push(c);
    });
    return Object.values(map).sort((a, b) => b.contacts.length - a.contacts.length);
  }, [contacts]);

  if (error) return (
    <div className="card" style={{ textAlign: "center", padding: "40px" }}>
      <h2 style={{ color: "var(--text-muted)" }}>⚠️ {error}</h2>
    </div>
  );

  return (
    <div>
      <div className="flex justify-between items-center" style={{ marginBottom: "32px" }}>
        <div>
          <h1>Lead Management</h1>
          <p style={{ color: "var(--text-muted)", fontSize: "14px", marginTop: "4px" }}>
            Manage your contacts and follow up with interested leads.
          </p>
        </div>
        <Link to="/add-contact">
          <button className="btn-primary"><Icons.Plus /> Add New Lead</button>
        </Link>
      </div>

      {/* SEARCH */}
      <div className="card" style={{ padding: "16px", marginBottom: "20px" }}>
        <div style={{ position: "relative" }}>
          <span style={{ position: "absolute", left: "12px", top: "10px", color: "var(--text-muted)" }}>
            <Icons.Search />
          </span>
          <input
            type="text"
            placeholder="Search leads by name or phone..."
            style={{ paddingLeft: "40px", marginBottom: 0 }}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* LABEL GROUP TABS */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "24px" }}>
        <button
          onClick={() => setActiveGroup("All")}
          style={{
            padding: "6px 16px",
            borderRadius: "20px",
            border: "1px solid",
            cursor: "pointer",
            fontSize: "13px",
            fontWeight: "600",
            background: activeGroup === "All" ? "var(--primary)" : "var(--bg-card)",
            color: activeGroup === "All" ? "#fff" : "var(--text-main)",
            borderColor: activeGroup === "All" ? "var(--primary)" : "var(--border)",
          }}
        >
          All
          <span style={{
            marginLeft: "6px",
            background: activeGroup === "All" ? "rgba(255,255,255,0.25)" : "var(--bg-main)",
            color: activeGroup === "All" ? "#fff" : "var(--text-muted)",
            borderRadius: "10px",
            padding: "1px 7px",
            fontSize: "11px",
          }}>
            {contacts.length}
          </span>
        </button>

        {labelGroups.map(([key, { label, count }]) => {
          const style = getTagStyle(key);
          const isActive = activeGroup === key;
          return (
            <button
              key={key}
              onClick={() => setActiveGroup(key)}
              style={{
                padding: "6px 16px",
                borderRadius: "20px",
                border: "1px solid",
                cursor: "pointer",
                fontSize: "13px",
                fontWeight: "600",
                background: isActive ? style.color : style.background,
                color: isActive ? "#fff" : style.color,
                borderColor: style.color,
              }}
            >
              {label}
              <span style={{
                marginLeft: "6px",
                background: isActive ? "rgba(255,255,255,0.25)" : style.color,
                color: "#fff",
                borderRadius: "10px",
                padding: "1px 7px",
                fontSize: "11px",
              }}>
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* CONTACTS TABLE */}
      <div style={{ marginBottom: "8px", color: "var(--text-muted)", fontSize: "13px" }}>
        Showing <strong>{Math.min(visibleCount, filteredContacts.length)}</strong> of <strong>{filteredContacts.length}</strong> contact{filteredContacts.length !== 1 ? "s" : ""}
        {activeGroup !== "All" && <> in <strong>{activeGroup}</strong></>}
      </div>

      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Phone Number</th>
              <th>Labels</th>
              <th style={{ textAlign: "right" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && contacts.length === 0 ? (
              <tr>
                <td colSpan="4" style={{ textAlign: "center", padding: "40px", color: "var(--text-muted)" }}>
                  Loading leads...
                </td>
              </tr>
            ) : filteredContacts.length === 0 ? (
              <tr>
                <td colSpan="4" style={{ textAlign: "center", padding: "40px", color: "var(--text-muted)" }}>
                  No leads found.
                </td>
              </tr>
            ) : (
              filteredContacts.slice(0, visibleCount).map(c => (
                <tr key={c.id}>
                  <td style={{ fontWeight: "600" }}>{c.name}</td>
                  <td style={{ color: "var(--text-muted)" }}>
                    <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <Icons.Phone /> {c.phone}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                      {c.tags
                        ? c.tags.split(",").map(tag => {
                            const s = getTagStyle(tag);
                            const isPopup = POPUP_TAGS.has(tag.trim().toLowerCase());
                            return (
                              <span
                                key={tag}
                                title={isPopup ? "Click to view" : undefined}
                                style={{
                                  ...s,
                                  borderRadius: "10px",
                                  padding: "2px 10px",
                                  fontSize: "11px",
                                  fontWeight: "600",
                                  cursor: "pointer",
                                  textDecoration: isPopup ? "underline dotted" : "none",
                                }}
                                onClick={() => handleTagClick(tag, c)}
                              >
                                {tag.trim()}
                              </span>
                            );
                          })
                        : <span style={{ color: "var(--text-muted)", fontSize: "12px" }}>—</span>
                      }
                    </div>
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <button className="btn-danger" style={{ padding: "6px" }} onClick={() => deleteContact(c.id)}>
                      <Icons.Trash />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {filteredContacts.length > visibleCount && (
        <div style={{ display: "flex", justifyContent: "center", marginTop: "16px" }}>
          <button className="btn-primary" onClick={() => setVisibleCount(v => v + 12)}>
            Show More ({filteredContacts.length - visibleCount} remaining)
          </button>
        </div>
      )}

      {/* GROUPED BY LABEL COMBINATION */}
      <div style={{ marginTop: "32px" }}>
        <h2 style={{ fontSize: "18px", marginBottom: "4px" }}>Grouped by Labels</h2>
        <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "16px" }}>
          Contacts grouped by their exact set of labels (e.g. "lead, course1" vs "lead, course2"). Click a group to expand.
        </p>
        <div className="card" style={{ padding: 0 }}>
          {comboGroups.map(group => {
            const isOpen = expandedCombos.has(group.key);
            return (
              <div key={group.key} style={{ borderTop: "1px solid var(--border)" }}>
                <div style={{ display: "flex", alignItems: "center" }}>
                  <button
                    onClick={() => toggleCombo(group.key)}
                    style={{
                      flex: 1,
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "14px 16px",
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      textAlign: "left",
                      color: "var(--text-main)",
                    }}
                  >
                    <span style={{ fontWeight: "600", fontSize: "14px" }}>{group.label}</span>
                    <span style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <span style={{
                        background: "var(--bg-main)",
                        color: "var(--text-muted)",
                        borderRadius: "10px",
                        padding: "2px 10px",
                        fontSize: "12px",
                        fontWeight: "600",
                      }}>
                        {group.contacts.length}
                      </span>
                      <span style={{ transform: isOpen ? "rotate(90deg)" : "none", transition: "transform 0.15s", display: "flex" }}>
                        <Icons.Chevron />
                      </span>
                    </span>
                  </button>
                  {group.tags.length > 0 && (
                    <button
                      className="btn-primary"
                      style={{ margin: "0 16px", padding: "6px 14px", fontSize: "12px", whiteSpace: "nowrap" }}
                      onClick={() => navigate("/create-campaign", { state: { targetTags: group.tags } })}
                    >
                      Run Campaign
                    </button>
                  )}
                </div>
                {isOpen && (
                  <div style={{ padding: "0 16px 16px" }}>
                    <table>
                      <thead>
                        <tr>
                          <th>Name</th>
                          <th>Phone Number</th>
                          <th>Labels</th>
                        </tr>
                      </thead>
                      <tbody>
                        {group.contacts.map(c => (
                          <tr key={c.id}>
                            <td style={{ fontWeight: "600" }}>{c.name}</td>
                            <td style={{ color: "var(--text-muted)" }}>{c.phone}</td>
                            <td style={{ color: "var(--text-muted)", fontSize: "12px" }}>{c.tags || "—"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {detailsModal && (
        <Modal
          title={`Scholarship Details — ${detailsModal.contact.name}`}
          onClose={() => setDetailsModal(null)}
        >
          {detailsModal.error ? (
            <p style={{ color: "var(--text-muted)" }}>{detailsModal.error}</p>
          ) : !detailsModal.data ? (
            <p style={{ color: "var(--text-muted)" }}>Loading...</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "14px" }}>
              <div><strong>Name:</strong> {detailsModal.data.name || "—"}</div>
              <div><strong>Phone:</strong> {detailsModal.data.phone_number || "—"}</div>
              <div><strong>Email:</strong> {detailsModal.data.email || "—"}</div>
              <div><strong>Location:</strong> {detailsModal.data.location || "—"}</div>
              <div><strong>Qualification:</strong> {detailsModal.data.qualification || "—"}</div>
            </div>
          )}
        </Modal>
      )}

      {idProofModal && (
        <Modal
          title={`ID Proof — ${idProofModal.contact.name}`}
          onClose={closeIdProofModal}
        >
          {idProofModal.error ? (
            <p style={{ color: "var(--text-muted)" }}>{idProofModal.error}</p>
          ) : !idProofModal.imageUrl ? (
            <p style={{ color: "var(--text-muted)" }}>Loading...</p>
          ) : (
            <img src={idProofModal.imageUrl} alt="ID proof" style={{ width: "100%", borderRadius: "8px" }} />
          )}
        </Modal>
      )}
    </div>
  );
}
