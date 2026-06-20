import { useEffect, useState } from "react";
import api from "../api";
import { useNavigate, useLocation, Link } from "react-router-dom";

const Icons = {
  ChevronLeft: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
  ),
  Upload: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
  )
};

export default function CreateCampaign() {
  const [templates, setTemplates] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [template, setTemplate] = useState("");
  const [tag, setTag] = useState("");
  const [message, setMessage] = useState("");
  const [variables, setVariables] = useState([]);
  const [imageFile, setImageFile] = useState(null);
  const [imageUrl, setImageUrl] = useState("");
  const [posters, setPosters] = useState([]);
  const [showGallery, setShowGallery] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const [targetTags, setTargetTags] = useState(location.state?.targetTags || null);

  useEffect(() => {
    api.get("/templates")
      .then(res => setTemplates(res.data))
      .catch(err => console.error("Could not fetch templates", err));
      
    api.get("/contacts")
      .then(res => setContacts(res.data))
      .catch(err => console.error("Could not fetch contacts", err));

    api.get("/campaigns/posters")
      .then(res => setPosters(res.data))
      .catch(err => console.error("Could not fetch posters", err));
  }, []);

  const pickPoster = (url) => {
    setImageUrl(url);
    setImageFile(null);
    setShowGallery(false);
  };

  const getVariableFields = () => {
    const t = templates.find(temp => temp.name === template);
    return (t && t.variables) || null;
  };

  useEffect(() => {
    const fields = getVariableFields();
    setVariables(fields ? Array(fields.length).fill("") : []);
  }, [template, templates]);

  const updateVariable = (idx, value) => {
    setVariables(prev => {
      const next = [...prev];
      next[idx] = value;
      return next;
    });
  };

  const getUniqueTags = () => {
    const allTags = new Set();
    contacts.forEach(c => {
      if (c.tags) {
        c.tags.split(",").forEach(t => allTags.add(t.trim()));
      }
    });
    return Array.from(allTags).sort();
  };

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const formData = new FormData();
    formData.append("template_name", template);
    if (targetTags) {
      formData.append("tags", targetTags.join(","));
    } else {
      formData.append("tag", tag);
    }
    const variableFields = getVariableFields();
    if (variableFields) {
      formData.append("variables", JSON.stringify(variables));
    } else {
      formData.append("message", message);
    }

    if (imageFile) {
        formData.append("image", imageFile);
    } else {
        formData.append("image_url", imageUrl);
    }

    try {
      await api.post("/campaigns", formData, {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
      });
      navigate("/campaigns");
    } catch (err) {
      alert("Error creating campaign.");
    } finally {
      setLoading(false);
    }
  };

  // Check if current selected template needs an image field
  const needsImage = () => {
    const t = templates.find(temp => temp.name === template);
    return template === "CUSTOM_IMAGE" || (t && t.type === "image");
  };

  return (
    <div style={{ maxWidth: "800px", margin: "0 auto" }}>
      <div style={{ marginBottom: "24px" }}>
        <Link to="/campaigns" style={{ display: "flex", alignItems: "center", gap: "4px", color: "var(--text-muted)", fontSize: "14px", fontWeight: "500" }}>
          <Icons.ChevronLeft /> Back to Campaigns
        </Link>
      </div>

      <div style={{ marginBottom: "32px" }}>
        <h1>Launch New Campaign</h1>
        <p style={{ color: "var(--text-muted)", fontSize: "14px", marginTop: "4px" }}>Create a broadcast to reach your contacts on WhatsApp.</p>
      </div>

      <div className="card">
        <form onSubmit={submit}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginBottom: "24px" }}>
            <div>
              <label style={{ display: "block", marginBottom: "8px", fontWeight: "600", fontSize: "14px" }}>Content Type</label>
              <select onChange={e => setTemplate(e.target.value)} required value={template} style={{ marginBottom: 0 }}>
                <option value="">-- Choose template --</option>
                {templates.map(t => (
                  <option key={t.name} value={t.name}>{t.label}</option>
                ))}
                <option value="CUSTOM_TEXT">Custom Text (Within 24hr Window)</option>
                <option value="CUSTOM_IMAGE">Custom Image (Within 24hr Window)</option>
              </select>
            </div>
            <div>
              <label style={{ display: "block", marginBottom: "8px", fontWeight: "600", fontSize: "14px" }}>Target Segment (Tag)</label>
              {targetTags ? (
                <div style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  padding: "8px 12px", background: "var(--bg-main)", borderRadius: "var(--radius)",
                  border: "1px solid var(--border)", fontSize: "13px",
                }}>
                  <span>Contacts with: <strong>{targetTags.join(", ")}</strong></span>
                  <button type="button" onClick={() => setTargetTags(null)} className="btn-outline" style={{ padding: "2px 10px", fontSize: "12px" }}>
                    Change
                  </button>
                </div>
              ) : (
                <select onChange={e => setTag(e.target.value)} value={tag} style={{ marginBottom: 0 }}>
                  <option value="">All Contacts</option>
                  {getUniqueTags().map(t => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              )}
            </div>
          </div>

          {needsImage() && (
            <div style={{ marginBottom: "24px", padding: "24px", background: "var(--bg-main)", borderRadius: "var(--radius)", border: "1px dashed var(--border)" }}>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center" }}>
                <div style={{ color: "var(--primary)", marginBottom: "12px" }}><Icons.Upload /></div>
                <div style={{ fontWeight: "600", marginBottom: "4px" }}>Upload Poster Image</div>
                <p style={{ color: "var(--text-muted)", fontSize: "12px", marginBottom: "16px" }}>PNG, JPG, or WEBP up to 5MB</p>
                <input
                  type="file"
                  accept="image/*"
                  onChange={e => {
                    setImageFile(e.target.files[0]);
                    if (e.target.files[0]) setImageUrl(""); // Clear URL if file is picked
                  }}
                  required={!imageUrl}
                  style={{ fontSize: "12px", width: "auto", margin: "0 auto" }}
                />
              </div>
              
              <div style={{ display: "flex", alignItems: "center", gap: "16px", margin: "20px 0" }}>
                <div style={{ flex: 1, height: "1px", background: "var(--border)" }}></div>
                <div style={{ color: "var(--text-muted)", fontSize: "12px", fontWeight: "600" }}>OR</div>
                <div style={{ flex: 1, height: "1px", background: "var(--border)" }}></div>
              </div>

              <label style={{ display: "block", marginBottom: "8px", fontWeight: "600", fontSize: "14px" }}>Image Link (URL)</label>
              <input
                placeholder="https://example.com/your-poster.jpg"
                value={imageUrl}
                onChange={e => {
                  setImageUrl(e.target.value);
                  if (e.target.value) setImageFile(null); // Clear file if URL is typed
                }}
                disabled={!!imageFile}
                style={{ marginBottom: 0 }}
              />

              <button
                type="button"
                className="btn-outline"
                onClick={() => setShowGallery(s => !s)}
                style={{ marginTop: "16px", fontSize: "13px" }}
              >
                {showGallery ? "Hide uploaded images" : `Browse uploaded images (${posters.length})`}
              </button>

              {showGallery && (
                <div style={{
                  display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(100px, 1fr))", gap: "10px",
                  marginTop: "16px", maxHeight: "260px", overflowY: "auto", padding: "4px"
                }}>
                  {posters.length === 0 && (
                    <p style={{ color: "var(--text-muted)", fontSize: "13px", gridColumn: "1 / -1" }}>No images uploaded yet.</p>
                  )}
                  {posters.map(p => (
                    <img
                      key={p.filename}
                      src={p.url}
                      alt={p.filename}
                      onClick={() => pickPoster(p.url)}
                      style={{
                        width: "100%", height: "90px", objectFit: "cover", borderRadius: "var(--radius)",
                        cursor: "pointer", border: imageUrl === p.url ? "2px solid var(--primary)" : "2px solid transparent"
                      }}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {getVariableFields() ? (
            <div style={{ marginBottom: "24px" }}>
              <label style={{ display: "block", marginBottom: "8px", fontWeight: "600", fontSize: "14px" }}>Template Variables</label>
              {getVariableFields().map((fieldLabel, idx) => (
                <div key={idx} style={{ marginBottom: "12px" }}>
                  <label style={{ display: "block", marginBottom: "4px", fontSize: "13px", color: "var(--text-muted)" }}>{fieldLabel}</label>
                  <textarea
                    placeholder={fieldLabel}
                    value={variables[idx] || ""}
                    onChange={e => updateVariable(idx, e.target.value)}
                    required
                    style={{ height: "60px", marginBottom: 0, resize: "vertical" }}
                  />
                </div>
              ))}
            </div>
          ) : (
            <div style={{ marginBottom: "24px" }}>
              <label style={{ display: "block", marginBottom: "8px", fontWeight: "600", fontSize: "14px" }}>Message Content</label>
              <textarea
                placeholder="Type your campaign text here..."
                value={message}
                onChange={e => setMessage(e.target.value)}
                required
                style={{ height: "160px", marginBottom: 0, resize: "vertical" }}
              />
            </div>
          )}

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px" }}>
            <Link to="/campaigns">
              <button type="button" className="btn-outline">Cancel</button>
            </Link>
            <button type="submit" className="btn-primary" style={{ minWidth: "160px" }} disabled={loading}>
              {loading ? "Launching..." : "Launch Campaign"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}