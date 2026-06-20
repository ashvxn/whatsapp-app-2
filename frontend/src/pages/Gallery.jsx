import { useEffect, useState } from "react";
import api from "../api";

export default function Gallery() {
  const [posters, setPosters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [copiedUrl, setCopiedUrl] = useState("");

  useEffect(() => {
    api.get("/campaigns/posters")
      .then(res => setPosters(res.data))
      .catch(err => console.error("Could not fetch posters", err))
      .finally(() => setLoading(false));
  }, []);

  const copyLink = (url) => {
    navigator.clipboard.writeText(url);
    setCopiedUrl(url);
    setTimeout(() => setCopiedUrl(""), 1500);
  };

  return (
    <div>
      <div style={{ marginBottom: "32px" }}>
        <h1>Image Gallery</h1>
        <p style={{ color: "var(--text-muted)", fontSize: "14px", marginTop: "4px" }}>
          All posters previously uploaded for campaigns. Copy a link to reuse it.
        </p>
      </div>

      {loading ? (
        <p style={{ color: "var(--text-muted)" }}>Loading images...</p>
      ) : posters.length === 0 ? (
        <p style={{ color: "var(--text-muted)" }}>No images uploaded yet.</p>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "20px" }}>
          {posters.map(p => (
            <div key={p.filename} className="card" style={{ padding: "12px" }}>
              <img
                src={p.url}
                alt={p.filename}
                style={{ width: "100%", height: "160px", objectFit: "cover", borderRadius: "var(--radius)", marginBottom: "10px" }}
              />
              <button
                type="button"
                className="btn-outline"
                onClick={() => copyLink(p.url)}
                style={{ width: "100%", fontSize: "13px" }}
              >
                {copiedUrl === p.url ? "Copied!" : "Copy Link"}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
