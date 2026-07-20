import { useState, useEffect, useRef, useCallback } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ─── Design tokens ────────────────────────────────────────────────────────────
// Palette: deep navy base, molten amber accent, critical red, safe teal
// Type: Inter for data/UI, monospace for values/IDs
// Signature: the "pulse ring" on critical assets — the one thing judges remember

const css = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg-0:       #0b0f1a;
    --bg-1:       #111827;
    --bg-2:       #1a2235;
    --bg-3:       #243044;
    --border:     #2a3a52;
    --amber:      #f59e0b;
    --amber-dim:  #92600a;
    --amber-glow: rgba(245,158,11,0.12);
    --red:        #ef4444;
    --red-glow:   rgba(239,68,68,0.15);
    --teal:       #14b8a6;
    --teal-glow:  rgba(20,184,166,0.12);
    --yellow:     #eab308;
    --text-0:     #f1f5f9;
    --text-1:     #94a3b8;
    --text-2:     #64748b;
    --mono:       'JetBrains Mono', monospace;
    --sans:       'Inter', sans-serif;
    --radius:     10px;
    --radius-lg:  16px;
    --transition: 200ms ease;
  }

  html, body, #root { height: 100%; margin: 0; }

  body {
    font-family: var(--sans);
    background: transparent;
    color: var(--text-0);
    font-size: 14px;
    line-height: 1.5;
    overflow-x: hidden;
    /* Custom Cursors */
    cursor: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="%23f59e0b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><line x1="12" y1="2" x2="12" y2="7"></line><line x1="12" y1="17" x2="12" y2="22"></line><line x1="2" y1="12" x2="7" y2="12"></line><line x1="17" y1="12" x2="22" y2="12"></line></svg>') 12 12, auto;
  }

  a, button, .nav-item, input, select, .kpi-card, .btn {
    cursor: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="%2314b8a6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>') 12 12, pointer !important;
  }

  .vanta-bg {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    z-index: -1;
  }

  .app { display: flex; height: 100vh; overflow: hidden; background: transparent; }

  /* ── Sidebar ── */
  .sidebar {
    width: 220px;
    min-width: 220px;
    background: rgba(17, 24, 39, 0.25);
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
    display: flex;
    flex-direction: column;
    padding: 0;
    overflow-y: auto;
  }
  .sidebar-logo {
    padding: 20px 16px 16px;
    border-bottom: 1px solid var(--border);
  }
  .logo-mark {
    font-family: var(--mono);
    font-size: 18px;
    font-weight: 500;
    color: var(--amber);
    letter-spacing: -0.5px;
  }
  .logo-sub {
    font-size: 10px;
    color: var(--text-2);
    margin-top: 2px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }
  .nav { padding: 12px 8px; flex: 1; }
  .nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 10px;
    border-radius: var(--radius);
    cursor: pointer;
    color: var(--text-1);
    font-size: 13px;
    font-weight: 400;
    transition: all var(--transition);
    margin-bottom: 2px;
    border: 1px solid transparent;
  }
  .nav-item:hover { background: var(--bg-2); color: var(--text-0); }
  .nav-item.active {
    background: var(--amber-glow);
    color: var(--amber);
    border-color: var(--amber-dim);
    font-weight: 500;
  }
  .nav-icon { font-size: 16px; width: 20px; text-align: center; }
  .sidebar-footer {
    padding: 12px 16px;
    border-top: 1px solid var(--border);
  }
  .status-dot {
    display: inline-block;
    width: 7px; height: 7px;
    border-radius: 50%;
    background: var(--teal);
    margin-right: 6px;
    box-shadow: 0 0 6px var(--teal);
    animation: pulse-teal 2s infinite;
  }
  @keyframes pulse-teal {
    0%,100% { box-shadow: 0 0 4px var(--teal); }
    50%      { box-shadow: 0 0 10px var(--teal); }
  }
  .status-label { font-size: 11px; color: var(--text-2); }

  /* ── Main ── */
  .main {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
  }
  .topbar {
    padding: 14px 28px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    background: rgba(17, 24, 39, 0.25);
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 10;
  }
  .topbar-title { font-size: 16px; font-weight: 600; }
  .topbar-meta { font-size: 12px; color: var(--text-2); font-family: var(--mono); }
  .page { padding: 24px 28px; flex: 1; }

  /* ── Cards ── */
  .card {
    background: rgba(17, 24, 39, 0.25);
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    border-radius: var(--radius-lg);
    padding: 20px;
  }
  .card-title {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--text-2);
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  /* ── Grid ── */
  .grid-4 { display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; }
  .grid-2 { display: grid; grid-template-columns: repeat(2,1fr); gap: 14px; }
  .grid-3 { display: grid; grid-template-columns: repeat(3,1fr); gap: 14px; }

  /* ── KPI cards ── */
  .kpi-card {
    background: rgba(17, 24, 39, 0.25);
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    border-radius: var(--radius-lg);
    padding: 18px;
    position: relative;
    overflow: hidden;
  }
  .kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
  }
  .kpi-card.amber::before { background: var(--amber); }
  .kpi-card.red::before   { background: var(--red); }
  .kpi-card.teal::before  { background: var(--teal); }
  .kpi-card.yellow::before { background: var(--yellow); }
  .kpi-label { font-size: 11px; color: var(--text-2); text-transform: uppercase; letter-spacing: 0.5px; }
  .kpi-value { font-family: var(--mono); font-size: 32px; font-weight: 500; margin: 6px 0 2px; line-height: 1; }
  .kpi-value.amber { color: var(--amber); }
  .kpi-value.red   { color: var(--red); }
  .kpi-value.teal  { color: var(--teal); }
  .kpi-value.yellow { color: var(--yellow); }
  .kpi-sub { font-size: 11px; color: var(--text-2); }

  /* ── CRITICAL pulse ring (signature element) ── */
  .pulse-ring {
    position: relative;
    display: inline-block;
    width: 10px; height: 10px;
    margin-right: 8px;
    vertical-align: middle;
  }
  .pulse-ring::before, .pulse-ring::after {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 50%;
    background: var(--red);
  }
  .pulse-ring::after {
    animation: ring-pulse 1.6s ease-out infinite;
    background: transparent;
    border: 2px solid var(--red);
  }
  @keyframes ring-pulse {
    0%   { transform: scale(1);   opacity: 0.8; }
    100% { transform: scale(2.8); opacity: 0; }
  }

  /* ── Buttons ── */
  .btn {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 9px 18px;
    border-radius: var(--radius);
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--transition);
    border: none;
    font-family: var(--sans);
  }
  .btn-primary {
    background: var(--amber);
    color: #000;
  }
  .btn-primary:hover { background: #fbbf24; }
  .btn-primary:disabled { opacity: 0.45; cursor: not-allowed; }
  .btn-ghost {
    background: transparent;
    color: var(--text-1);
    border: 1px solid var(--border);
  }
  .btn-ghost:hover { background: var(--bg-2); color: var(--text-0); }
  .btn-danger {
    background: var(--red-glow);
    color: var(--red);
    border: 1px solid rgba(239,68,68,0.3);
  }

  /* ── Inputs ── */
  input, textarea, select {
    font-family: var(--sans);
    font-size: 13px;
    background: var(--bg-2);
    border: 1px solid var(--border);
    color: var(--text-0);
    border-radius: var(--radius);
    padding: 9px 13px;
    width: 100%;
    outline: none;
    transition: border-color var(--transition);
  }
  input:focus, textarea:focus, select:focus { border-color: var(--amber); }
  textarea { resize: vertical; min-height: 80px; }
  label { font-size: 12px; color: var(--text-1); margin-bottom: 6px; display: block; }

  /* ── Badges ── */
  .badge {
    display: inline-flex;
    align-items: center;
    padding: 3px 9px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    font-family: var(--mono);
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }
  .badge-critical { background: rgba(239,68,68,0.15); color: var(--red);    border: 1px solid rgba(239,68,68,0.3); }
  .badge-high     { background: rgba(245,158,11,0.15); color: var(--amber); border: 1px solid rgba(245,158,11,0.3); }
  .badge-medium   { background: rgba(234,179,8,0.15);  color: var(--yellow);border: 1px solid rgba(234,179,8,0.3); }
  .badge-low      { background: rgba(20,184,166,0.15); color: var(--teal);  border: 1px solid rgba(20,184,166,0.3); }

  /* ── Confidence Meter ── */
  .conf-meter { margin-top: 16px; }
  .conf-overall {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }
  .conf-pct {
    font-family: var(--mono);
    font-size: 28px;
    font-weight: 500;
    color: var(--amber);
  }
  .conf-label { font-size: 11px; color: var(--text-2); text-transform: uppercase; letter-spacing: 0.5px; }
  .conf-bar-row { margin-bottom: 8px; }
  .conf-bar-label { display: flex; justify-content: space-between; margin-bottom: 4px; }
  .conf-bar-name  { font-size: 11px; color: var(--text-1); }
  .conf-bar-val   { font-family: var(--mono); font-size: 11px; color: var(--text-2); }
  .conf-bar-track {
    height: 5px;
    background: var(--bg-3);
    border-radius: 3px;
    overflow: hidden;
  }
  .conf-bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.8s cubic-bezier(0.4,0,0.2,1);
  }

  /* ── Evidence citations ── */
  .citation {
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-left: 3px solid var(--amber);
    border-radius: var(--radius);
    padding: 12px 14px;
    margin-bottom: 8px;
  }
  .citation-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px; }
  .citation-source { font-size: 12px; font-weight: 600; color: var(--amber); font-family: var(--mono); }
  .citation-section { font-size: 11px; color: var(--text-2); margin-top: 2px; }
  .citation-excerpt { font-size: 12px; color: var(--text-1); line-height: 1.6; }

  /* ── Sensor sliders ── */
  .sensor-grid { display: grid; grid-template-columns: repeat(2,1fr); gap: 14px; }
  .sensor-item { }
  .sensor-header { display: flex; justify-content: space-between; margin-bottom: 6px; }
  .sensor-name { font-size: 12px; color: var(--text-1); }
  .sensor-val { font-family: var(--mono); font-size: 13px; font-weight: 500; }
  .sensor-val.danger { color: var(--red); }
  .sensor-val.warn   { color: var(--amber); }
  .sensor-val.ok     { color: var(--teal); }
  input[type=range] {
    padding: 0;
    height: 4px;
    accent-color: var(--amber);
    cursor: pointer;
    border: none;
    background: var(--bg-3);
    border-radius: 2px;
  }

  /* ── Response area ── */
  .response-box {
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 20px;
    font-size: 13px;
    line-height: 1.8;
    color: var(--text-0);
    white-space: pre-wrap;
    max-height: 400px;
    overflow-y: auto;
  }
  .response-box strong { color: var(--amber); }

  /* ── Upload zone ── */
  .upload-zone {
    border: 2px dashed var(--border);
    border-radius: var(--radius-lg);
    padding: 40px 20px;
    text-align: center;
    cursor: pointer;
    transition: all var(--transition);
    background: var(--bg-2);
  }
  .upload-zone:hover, .upload-zone.dragover {
    border-color: var(--amber);
    background: var(--amber-glow);
  }
  .upload-icon { font-size: 36px; margin-bottom: 12px; }
  .upload-text { color: var(--text-1); font-size: 14px; }
  .upload-sub  { color: var(--text-2); font-size: 12px; margin-top: 6px; }

  /* ── Table ── */
  .data-table { width: 100%; border-collapse: collapse; }
  .data-table th {
    text-align: left;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-2);
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
    font-weight: 600;
  }
  .data-table td {
    padding: 11px 14px;
    font-size: 13px;
    border-bottom: 1px solid rgba(42,58,82,0.5);
    color: var(--text-1);
  }
  .data-table tr:hover td { background: var(--bg-2); color: var(--text-0); }
  .mono-cell { font-family: var(--mono); color: var(--text-0); }

  /* ── Misc ── */
  .section-gap { margin-bottom: 20px; }
  .rule-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 14px;
    background: var(--red-glow);
    border: 1px solid rgba(239,68,68,0.25);
    border-radius: var(--radius);
    margin-bottom: 8px;
    font-size: 12px;
    color: var(--text-0);
  }
  .empty-state { text-align: center; padding: 48px; color: var(--text-2); }
  .empty-icon  { font-size: 40px; margin-bottom: 12px; }
  .spinner {
    width: 18px; height: 18px;
    border: 2px solid var(--border);
    border-top-color: var(--amber);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    display: inline-block;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .tag {
    display: inline-block;
    padding: 2px 8px;
    background: var(--bg-3);
    border-radius: 4px;
    font-size: 11px;
    color: var(--text-1);
    font-family: var(--mono);
    margin-right: 4px;
    margin-bottom: 4px;
  }
  .divider { border: none; border-top: 1px solid var(--border); margin: 20px 0; }
  .ml-grid { display: grid; grid-template-columns: repeat(2,1fr); gap: 10px; }
  .ml-stat {
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 12px 14px;
  }
  .ml-stat-label { font-size: 11px; color: var(--text-2); margin-bottom: 4px; }
  .ml-stat-val { font-family: var(--mono); font-size: 18px; font-weight: 500; }
  .feature-bar { margin-bottom: 6px; }
  .feature-bar-header { display: flex; justify-content: space-between; margin-bottom: 3px; font-size: 11px; }
  .feature-bar-name { color: var(--text-1); }
  .feature-bar-pct  { color: var(--amber); font-family: var(--mono); }
  .feature-track { height: 4px; background: var(--bg-3); border-radius: 2px; }
  .feature-fill  { height: 100%; background: var(--amber); border-radius: 2px; transition: width 0.6s ease; }
`;

// ─── Nav config ──────────────────────────────────────────────────────────────
const NAV = [
  { id: "dashboard", icon: "⬡", label: "Dashboard"   },
  { id: "query",     icon: "⟳", label: "Query Engine" },
  { id: "ingest",    icon: "↑", label: "Ingest Docs"  },
  { id: "kg",        icon: "◈", label: "Knowledge Graph" },
  { id: "predict",   icon: "◉", label: "Predict"      },
];

const RISK_COLOR = { CRITICAL: "red", HIGH: "amber", MEDIUM: "yellow", LOW: "teal" };
const CONF_COLORS = ["#f59e0b","#14b8a6","#818cf8","#64748b"];

// ─── App ─────────────────────────────────────────────────────────────────────
export default function App() {
  const [page, setPage] = useState("dashboard");
  const [health, setHealth] = useState(null);
  const [vantaEffect, setVantaEffect] = useState(null);
  const myRef = useRef(null);

  useEffect(() => {
    fetch(`${API}/health`).then(r => r.json()).then(setHealth).catch(() => {});
  }, []);

  useEffect(() => {
    if (!vantaEffect && window.VANTA) {
      setVantaEffect(window.VANTA.NET({
        el: myRef.current,
        mouseControls: true,
        touchControls: true,
        gyroControls: false,
        minHeight: 200.00,
        minWidth: 200.00,
        scale: 1.00,
        scaleMobile: 1.00,
        color: 0xf59e0b,
        backgroundColor: 0x070b14,
        points: 16.00,
        maxDistance: 24.00,
        spacing: 14.00,
        showDots: true
      }));
    }
    return () => {
      if (vantaEffect) vantaEffect.destroy();
    }
  }, [vantaEffect]);

  return (
    <>
      <style>{css}</style>
      <div className="vanta-bg" ref={myRef}></div>
      <div className="app">
        <Sidebar page={page} setPage={setPage} health={health} />
        <div className="main">
          <Topbar page={page} health={health} />
          <div className="page">
            {page === "dashboard" && <DashboardPage />}
            {page === "query"     && <QueryPage />}
            {page === "ingest"    && <IngestPage />}
            {page === "kg"        && <KGPage />}
            {page === "predict"   && <PredictPage />}
          </div>
        </div>
      </div>
    </>
  );
}

// ─── Sidebar ─────────────────────────────────────────────────────────────────
function Sidebar({ page, setPage, health }) {
  return (
    <div className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-mark">⚙ Kaizen AI</div>
        <div className="logo-sub">Industrial Intelligence</div>
      </div>
      <nav className="nav">
        {NAV.map(n => (
          <div key={n.id}
               className={`nav-item ${page === n.id ? "active" : ""}`}
               onClick={() => setPage(n.id)}>
            <span className="nav-icon">{n.icon}</span>
            {n.label}
          </div>
        ))}
      </nav>
      <div className="sidebar-footer">
        <span className="status-dot"></span>
        <span className="status-label">
          {health ? `${health.chunks_indexed} chunks · ${health.kg_nodes} KG nodes` : "Connecting..."}
        </span>
      </div>
    </div>
  );
}

function Topbar({ page, health }) {
  const label = NAV.find(n => n.id === page)?.label || "";
  return (
    <div className="topbar">
      <div className="topbar-title">{label}</div>
      <div className="topbar-meta">
        {health ? `${health.docs_ingested} docs ingested · ML ${health.ml_trained ? "ready" : "training"}` : "—"}
      </div>
    </div>
  );
}

// ─── Dashboard ────────────────────────────────────────────────────────────────
function DashboardPage() {
  const [data, setData] = useState(null);
  useEffect(() => {
    fetch(`${API}/dashboard`).then(r => r.json()).then(setData).catch(() => {});
  }, []);

  if (!data) return <Loading text="Loading dashboard..." />;
  const s = data.summary;

  return (
    <div>
      <div className="grid-4 section-gap">
        <KPI label="Total Assets" value={s.total_assets} color="teal" sub="registered in KG" />
        <KPI label="Critical Alerts" value={s.critical_alerts} color="red" sub="immediate action" pulse={s.critical_alerts > 0} />
        <KPI label="Docs Indexed" value={s.docs_ingested} color="amber" sub={`${s.chunks_indexed} chunks`} />
        <KPI label="Compliance" value={`${s.compliance_score}%`} color="teal" sub="audit readiness" />
      </div>

      <div className="grid-2 section-gap">
        <div className="card">
          <div className="card-title">⬡ Knowledge Graph</div>
          <div className="grid-2" style={{gap:10}}>
            {Object.entries(data.kg_breakdown || {}).map(([k,v]) => (
              <div key={k} className="ml-stat">
                <div className="ml-stat-label">{k}</div>
                <div className="ml-stat-val" style={{color:"var(--amber)",fontSize:22}}>{v}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="card-title">◈ Risk Distribution</div>
          {Object.entries(data.risk_distribution || {}).map(([level, count]) => (
            <div key={level} style={{marginBottom:10}}>
              <div style={{display:"flex",justifyContent:"space-between",marginBottom:4}}>
                <span style={{fontSize:12}}>{level === "CRITICAL" && <><span className="pulse-ring"></span></>}{level}</span>
                <span className={`badge badge-${level.toLowerCase()}`} style={{padding:"1px 8px"}}>{count}</span>
              </div>
              <div className="conf-bar-track">
                <div className="conf-bar-fill"
                     style={{
                       width:`${Math.min(100,(count/Math.max(1,s.total_assets))*100)}%`,
                       background: level==="CRITICAL"?"var(--red)":level==="HIGH"?"var(--amber)":level==="MEDIUM"?"var(--yellow)":"var(--teal)"
                     }}/>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="card-title">↑ Recently Ingested Documents</div>
        {data.recent_docs?.length ? (
          <table className="data-table">
            <thead><tr>
              <th>Filename</th><th>Type</th><th>Chunks</th><th>Trust</th><th>Revision</th><th>Ingested</th>
            </tr></thead>
            <tbody>
              {data.recent_docs.map((d,i) => (
                <tr key={i}>
                  <td className="mono-cell">{d.filename}</td>
                  <td><span className="tag">{d.doc_type}</span></td>
                  <td className="mono-cell">{d.chunks}</td>
                  <td>
                    <span style={{color: d.trust_score>0.85?"var(--teal)":d.trust_score>0.65?"var(--amber)":"var(--red)"}}>
                      {d.trust_score ? (d.trust_score*100).toFixed(0)+"%" : "—"}
                    </span>
                  </td>
                  <td className="mono-cell">{d.revision || "—"}</td>
                  <td style={{color:"var(--text-2)",fontSize:11}}>{d.timestamp?.slice(0,16).replace("T"," ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <div className="empty-state"><div className="empty-icon">↑</div>No documents ingested yet. Upload documents to begin.</div>}
      </div>
    </div>
  );
}

function KPI({ label, value, color, sub, pulse }) {
  return (
    <div className={`kpi-card ${color}`}>
      <div className="kpi-label">
        {pulse && <span className="pulse-ring"></span>}
        {label}
      </div>
      <div className={`kpi-value ${color}`}>{value}</div>
      <div className="kpi-sub">{sub}</div>
    </div>
  );
}

// ─── Query Engine ─────────────────────────────────────────────────────────────
const DEMO_SENSORS = {
  vibration_mm_s: 7.8, temperature_c: 82, pressure_bar: 3.9,
  rpm: 1475, flow_rate_m3h: 79, lubrication_hours_since: 520, runtime_hours: 1650
};

function QueryPage() {
  const [query, setQuery] = useState("Pump P-104 vibration has increased to 7.8 mm/s. What is causing this and what should I do?");
  const [includeSensors, setIncludeSensors] = useState(true);
  const [sensors, setSensors] = useState(DEMO_SENSORS);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const run = async () => {
    if (!query.trim()) return;
    setLoading(true); setError(""); setResult(null);
    try {
      const body = { query, sensor_data: includeSensors ? sensors : null };
      const r = await fetch(`${API}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || "Query failed");
      setResult(data);
    } catch(e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const genWorkOrder = async () => {
    if (!result?.ml_summary) return;
    const ml = result.ml_summary;
    const body = {
      equipment_id: result.equipment_id || "P-104",
      equipment_name: "Centrifugal Feed Pump",
      priority: ml.risk_level,
      failure_type: ml.predicted_failure?.replace("_"," "),
      description: `AI-generated work order based on Industrial Reasoning Engine analysis.\nQuery: ${result.query}`,
      recommended_actions: [
        "Isolate pump and lock out/tag out before inspection",
        `Replace ${ml.predicted_failure?.replace("_"," ")} components`,
        "Check and re-lubricate bearing per OEM specification",
        "Align motor-pump coupling after reassembly",
        "Verify vibration <2.3 mm/s before return to service",
      ],
      spare_parts: ["SKF 6205 Bearing (2x)", "Mobil Grease XHP 222 (200g)", "Mechanical seal kit"],
      assigned_to: "Maintenance Team B",
      estimated_hours: 4,
      due_within_hours: ml.urgency_hours || 24,
      safety_precautions: ["LOTO required", "PPE mandatory", "Gas test before confined space entry"],
    };
    const r = await fetch(`${API}/workorder`, {
      method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(body)
    });
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url;
    a.download = "KaizenAI_WorkOrder.pdf"; a.click();
  };

  const SENSOR_META = {
    vibration_mm_s:          { label:"Vibration",        unit:"mm/s", min:0, max:15, warnAt:4.5, dangerAt:7.1 },
    temperature_c:           { label:"Temperature",      unit:"°C",   min:40,max:120,warnAt:75,  dangerAt:90  },
    pressure_bar:            { label:"Pressure",         unit:"bar",  min:0, max:8,  warnAt:2.5, dangerAt:1.5 },
    rpm:                     { label:"RPM",              unit:"rpm",  min:0, max:2000,warnAt:0,  dangerAt:0   },
    flow_rate_m3h:           { label:"Flow Rate",        unit:"m³/h", min:0, max:130, warnAt:65, dangerAt:50  },
    lubrication_hours_since: { label:"Lub. Interval",    unit:"hrs",  min:0, max:800, warnAt:400,dangerAt:500 },
    runtime_hours:           { label:"Runtime",          unit:"hrs",  min:0, max:5000,warnAt:0, dangerAt:0   },
  };

  const sensorColor = (key, val) => {
    const m = SENSOR_META[key];
    if (!m) return "ok";
    if (m.dangerAt && (key==="pressure_bar"?val<m.dangerAt:val>m.dangerAt)) return "danger";
    if (m.warnAt   && (key==="pressure_bar"?val<m.warnAt  :val>m.warnAt))   return "warn";
    return "ok";
  };

  return (
    <div>
      <div className="card section-gap">
        <div className="card-title">⟳ Industrial Reasoning Engine</div>
        <div style={{marginBottom:12}}>
          <label>Query</label>
          <textarea value={query} onChange={e=>setQuery(e.target.value)}
                    style={{height:72}} placeholder="Describe an equipment symptom or ask a maintenance question..." />
        </div>

        <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:16}}>
          <input type="checkbox" id="useSensors" checked={includeSensors}
                 onChange={e=>setIncludeSensors(e.target.checked)}
                 style={{width:"auto",padding:0}} />
          <label htmlFor="useSensors" style={{margin:0,cursor:"pointer"}}>Include live sensor readings</label>
        </div>

        {includeSensors && (
          <div className="sensor-grid" style={{marginBottom:16}}>
            {Object.entries(SENSOR_META).map(([key, meta]) => (
              <div className="sensor-item" key={key}>
                <div className="sensor-header">
                  <span className="sensor-name">{meta.label}</span>
                  <span className={`sensor-val ${sensorColor(key,sensors[key])}`}>
                    {sensors[key]} <span style={{fontSize:10,opacity:0.7}}>{meta.unit}</span>
                  </span>
                </div>
                <input type="range" min={meta.min} max={meta.max} step={meta.unit==="rpm"?5:0.1}
                       value={sensors[key]}
                       onChange={e=>setSensors(s=>({...s,[key]:parseFloat(e.target.value)}))} />
              </div>
            ))}
          </div>
        )}

        {error && <div style={{color:"var(--red)",fontSize:12,marginBottom:12}}>⚠ {error}</div>}
        <button className="btn btn-primary" onClick={run} disabled={loading}>
          {loading ? <><span className="spinner"></span> Reasoning...</> : "⟳ Run Reasoning Engine"}
        </button>
      </div>

      {result && <QueryResult result={result} onWorkOrder={genWorkOrder} />}
    </div>
  );
}

function QueryResult({ result, onWorkOrder }) {
  const conf = result.confidence || {};
  const ml   = result.ml_summary;
  const kg   = result.kg_summary;
  const confBars = [
    { name:"Document Evidence", val: conf.document_evidence, color:"var(--amber)" },
    { name:"Knowledge Graph",   val: conf.knowledge_graph,   color:"var(--teal)"  },
    { name:"ML Prediction",     val: conf.ml_prediction,     color:"#818cf8"      },
    { name:"Business Rules",    val: conf.business_rules,    color:"var(--text-2)"},
  ];

  return (
    <div>
      {/* Rules */}
      {result.rules_triggered?.length > 0 && (
        <div className="section-gap">
          {result.rules_triggered.map((r,i) => (
            <div className="rule-item" key={i}>
              <span className="pulse-ring"></span>
              <span>{r}</span>
            </div>
          ))}
        </div>
      )}

      <div className="grid-3 section-gap">
        {/* Confidence meter */}
        <div className="card">
          <div className="card-title">◎ Confidence Meter</div>
          <div className="conf-overall">
            <div>
              <div className="conf-label">Overall Confidence</div>
              <div className="conf-pct">{conf.overall}%</div>
            </div>
            <span className={`badge badge-${conf.interpretation?.toLowerCase() || "medium"}`}>
              {conf.interpretation}
            </span>
          </div>
          {confBars.map(b => (
            <div className="conf-bar-row" key={b.name}>
              <div className="conf-bar-label">
                <span className="conf-bar-name">{b.name}</span>
                <span className="conf-bar-val">{b.val}%</span>
              </div>
              <div className="conf-bar-track">
                <div className="conf-bar-fill" style={{width:`${b.val}%`,background:b.color}} />
              </div>
            </div>
          ))}
        </div>

        {/* ML Prediction */}
        {ml && (
          <div className="card">
            <div className="card-title">◉ ML Prediction</div>
            <div className="ml-grid">
              <div className="ml-stat">
                <div className="ml-stat-label">Failure Prob.</div>
                <div className="ml-stat-val" style={{color:"var(--red)"}}>{ml.failure_probability}</div>
              </div>
              <div className="ml-stat">
                <div className="ml-stat-label">RUL (days)</div>
                <div className="ml-stat-val" style={{color:"var(--amber)"}}>{ml.rul_days}</div>
              </div>
              <div className="ml-stat">
                <div className="ml-stat-label">Health Score</div>
                <div className="ml-stat-val" style={{color: ml.health_score<40?"var(--red)":ml.health_score<70?"var(--amber)":"var(--teal)"}}>
                  {ml.health_score}/100
                </div>
              </div>
              <div className="ml-stat">
                <div className="ml-stat-label">Risk Level</div>
                <div className={`badge badge-${ml.risk_level?.toLowerCase()}`} style={{marginTop:4}}>
                  {ml.risk_level}
                </div>
              </div>
            </div>
            <hr className="divider" />
            <div className="card-title" style={{marginBottom:8}}>Top Risk Factors</div>
            {Object.entries(ml.feature_contributions || {}).map(([k,v]) => (
              <div className="feature-bar" key={k}>
                <div className="feature-bar-header">
                  <span className="feature-bar-name">{k.replace(/_/g," ")}</span>
                  <span className="feature-bar-pct">{v}%</span>
                </div>
                <div className="feature-track">
                  <div className="feature-fill" style={{width:`${v}%`}} />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* KG summary */}
        {kg && (
          <div className="card">
            <div className="card-title">◈ Knowledge Graph Context</div>
            <div className="ml-grid" style={{marginBottom:12}}>
              <div className="ml-stat">
                <div className="ml-stat-label">Components</div>
                <div className="ml-stat-val" style={{color:"var(--teal)"}}>{kg.component_count}</div>
              </div>
              <div className="ml-stat">
                <div className="ml-stat-label">Past Failures</div>
                <div className="ml-stat-val" style={{color:"var(--red)"}}>{kg.failure_events}</div>
              </div>
            </div>
            {kg.recent_failures?.map((f,i) => (
              <div key={i} style={{background:"var(--red-glow)",border:"1px solid rgba(239,68,68,0.2)",borderRadius:6,padding:"8px 10px",marginBottom:6,fontSize:12}}>
                <span style={{color:"var(--red)",fontWeight:600}}>{f.failure}</span>
                {f.root_cause && <div style={{color:"var(--text-2)",marginTop:2}}>Cause: {f.root_cause}</div>}
              </div>
            ))}
            {kg.recent_maintenance?.map((m,i) => (
              <div key={i} style={{background:"var(--teal-glow)",border:"1px solid rgba(20,184,166,0.2)",borderRadius:6,padding:"8px 10px",marginBottom:6,fontSize:12}}>
                <span style={{color:"var(--teal)",fontWeight:600}}>{m.action}</span>
                <div style={{color:"var(--text-2)",marginTop:2}}>{m.date} · {m.technician}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* AI Explanation */}
      <div className="card section-gap">
        <div className="card-title" style={{justifyContent:"space-between",display:"flex",alignItems:"center"}}>
          <span>⟳ AI Reasoning — Explainable Output</span>
          {ml && (
            <button className="btn btn-primary" style={{fontSize:12,padding:"6px 14px"}} onClick={onWorkOrder}>
              ↓ Generate Work Order PDF
            </button>
          )}
        </div>
        <div className="response-box">
          {result.explanation || "No explanation generated."}
        </div>
      </div>

      {/* Citations */}
      {result.citations?.length > 0 && (
        <div className="card section-gap">
          <div className="card-title">📄 Document Evidence — Source Citations</div>
          {result.citations.map((c,i) => (
            <div className="citation" key={i}>
              <div className="citation-header">
                <div>
                  <div className="citation-source">📄 {c.source}</div>
                  <div className="citation-section">{c.section}</div>
                </div>
                <div style={{textAlign:"right"}}>
                  <div style={{fontSize:11,color:"var(--teal)"}}>Relevance: {c.relevance}</div>
                  <div style={{fontSize:11,color:"var(--text-2)"}}>Trust: {c.trust}{c.ocr?" · OCR":""}</div>
                </div>
              </div>
              <div className="citation-excerpt">{c.excerpt}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Ingest ───────────────────────────────────────────────────────────────────
function IngestPage() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [drag, setDrag] = useState(false);
  const fileRef = useRef();

  const upload = async (files) => {
    if (!files.length) return;
    setLoading(true);
    const fd = new FormData();
    Array.from(files).forEach(f => fd.append("files", f));
    try {
      const r = await fetch(`${API}/ingest`, { method:"POST", body: fd });
      const data = await r.json();
      setResults(data.results || []);
    } catch(e) { alert("Upload failed: " + e.message); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <div className="card section-gap">
        <div className="card-title">↑ Upload Industrial Documents</div>
        <div
          className={`upload-zone ${drag ? "dragover" : ""}`}
          onClick={() => fileRef.current.click()}
          onDragOver={e=>{e.preventDefault();setDrag(true)}}
          onDragLeave={()=>setDrag(false)}
          onDrop={e=>{e.preventDefault();setDrag(false);upload(e.dataTransfer.files)}}
        >
          {loading ? <><div className="spinner" style={{margin:"0 auto 12px"}}></div><div className="upload-text">Processing...</div></>
          : <>
              <div className="upload-icon">↑</div>
              <div className="upload-text">Drop documents here or click to browse</div>
              <div className="upload-sub">PDF · DOCX · XLSX · PNG · JPG — OEM manuals, maintenance logs, inspection reports, SOPs</div>
            </>}
          <input ref={fileRef} type="file" multiple accept=".pdf,.docx,.xlsx,.xls,.png,.jpg,.jpeg"
                 style={{display:"none"}} onChange={e=>upload(e.target.files)} />
        </div>
      </div>

      {results.length > 0 && (
        <div className="card">
          <div className="card-title">Ingestion Results</div>
          <table className="data-table">
            <thead><tr>
              <th>File</th><th>Type</th><th>Chunks</th><th>Entities</th>
              <th>Trust Score</th><th>Revision</th><th>Duplicate</th><th>Status</th>
            </tr></thead>
            <tbody>
              {results.map((r,i) => (
                <tr key={i}>
                  <td className="mono-cell" style={{fontSize:12}}>{r.filename}</td>
                  <td><span className="tag">{r.doc_type || "—"}</span></td>
                  <td className="mono-cell">{r.chunks ?? "—"}</td>
                  <td className="mono-cell">{r.entities ?? "—"}</td>
                  <td style={{color: r.trust_score>0.85?"var(--teal)":r.trust_score>0.65?"var(--amber)":"var(--red)"}}>
                    {r.trust_score ? (r.trust_score*100).toFixed(0)+"%" : "—"}
                  </td>
                  <td className="mono-cell">{r.revision || "—"}</td>
                  <td>{r.is_duplicate ? <span style={{color:"var(--amber)"}}>⚠ Dup</span> : <span style={{color:"var(--teal)"}}>✓</span>}</td>
                  <td>
                    {r.success
                      ? <span style={{color:"var(--teal)"}}>✓ Indexed</span>
                      : <span style={{color:"var(--red)"}}>✗ {r.error?.slice(0,30)}</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── KG Viewer ────────────────────────────────────────────────────────────────
function KGPage() {
  const [equipId, setEquipId] = useState("P-104");
  const [input, setInput] = useState("P-104");
  const iframeRef = useRef();
  const [kgUrl, setKgUrl] = useState(`${API}/kg/visualize?equipment_id=P-104`);
  const [ctx, setCtx] = useState(null);

  const load = () => {
    setKgUrl(`${API}/kg/visualize?equipment_id=${input}&t=${Date.now()}`);
    setEquipId(input);
    fetch(`${API}/kg/equipment/${input}`)
      .then(r=>r.json()).then(setCtx).catch(()=>setCtx(null));
  };

  useEffect(() => { load(); }, []);

  return (
    <div>
      <div className="card section-gap">
        <div className="card-title">◈ Knowledge Graph Explorer</div>
        <div style={{display:"flex",gap:10,marginBottom:16}}>
          <input value={input} onChange={e=>setInput(e.target.value.toUpperCase())}
                 placeholder="Equipment ID (e.g. P-104)"
                 style={{maxWidth:200}}
                 onKeyDown={e=>e.key==="Enter"&&load()} />
          <button className="btn btn-primary" onClick={load}>Load Graph</button>
          <button className="btn btn-ghost" onClick={()=>{setInput("");setKgUrl(`${API}/kg/visualize?t=${Date.now()}`)}}>
            Show All
          </button>
        </div>
        <div style={{borderRadius:var_radius_lg,overflow:"hidden",border:"1px solid var(--border)"}}>
          <iframe ref={iframeRef} src={kgUrl}
                  style={{width:"100%",height:480,border:"none",background:"transparent"}}
                  title="Knowledge Graph" />
        </div>
      </div>

      {ctx && (
        <div className="grid-3">
          <div className="card">
            <div className="card-title">⚙ Equipment</div>
            <div style={{fontSize:22,fontFamily:"var(--mono)",color:"var(--amber)",marginBottom:8}}>{equipId}</div>
            <div style={{fontSize:13,color:"var(--text-1)",marginBottom:12}}>
              {ctx.component_chain?.length} components · {ctx.failure_history?.length} failure events
            </div>
            {ctx.component_chain?.slice(0,5).map((c,i) => (
              <div key={i} className="tag" style={{display:"block",marginBottom:4}}>{c.component}</div>
            ))}
          </div>
          <div className="card">
            <div className="card-title" style={{color:"var(--red)"}}>⚠ Failure History</div>
            {ctx.failure_history?.length
              ? ctx.failure_history.slice(0,4).map((f,i) => (
                  <div key={i} style={{marginBottom:8,padding:"8px 10px",background:"var(--red-glow)",borderRadius:6,fontSize:12}}>
                    <div style={{color:"var(--red)",fontWeight:600}}>{f.failure}</div>
                    <div style={{color:"var(--text-2)",marginTop:3}}>{f.root_cause || "—"}</div>
                  </div>
                ))
              : <div style={{color:"var(--text-2)",fontSize:12}}>No recorded failures</div>}
          </div>
          <div className="card">
            <div className="card-title" style={{color:"var(--teal)"}}>🔧 Maintenance</div>
            {ctx.maintenance_history?.length
              ? ctx.maintenance_history.slice(0,4).map((m,i) => (
                  <div key={i} style={{marginBottom:8,padding:"8px 10px",background:"var(--teal-glow)",borderRadius:6,fontSize:12}}>
                    <div style={{color:"var(--teal)",fontWeight:600}}>{m.action}</div>
                    <div style={{color:"var(--text-2)",marginTop:3}}>{m.date} · {m.technician}</div>
                  </div>
                ))
              : <div style={{color:"var(--text-2)",fontSize:12}}>No maintenance records</div>}
          </div>
        </div>
      )}
    </div>
  );
}

// JS doesn't support CSS var() in style prop like that
const var_radius_lg = "16px";

// ─── Predict ──────────────────────────────────────────────────────────────────
function PredictPage() {
  const [form, setForm] = useState({
    equipment_id: "P-104",
    vibration_mm_s: 7.8,
    temperature_c: 82,
    pressure_bar: 3.9,
    rpm: 1475,
    flow_rate_m3h: 79,
    lubrication_hours_since: 520,
    runtime_hours: 1650,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/predict`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify(form)
      });
      setResult(await r.json());
    } catch(e) { alert(e.message); }
    finally { setLoading(false); }
  };

  const FIELDS = [
    {key:"vibration_mm_s",label:"Vibration (mm/s)",min:0,max:15,step:0.1},
    {key:"temperature_c",label:"Temperature (°C)",min:40,max:120,step:1},
    {key:"pressure_bar",label:"Pressure (bar)",min:0,max:8,step:0.1},
    {key:"rpm",label:"RPM",min:0,max:2000,step:10},
    {key:"flow_rate_m3h",label:"Flow Rate (m³/h)",min:0,max:130,step:1},
    {key:"lubrication_hours_since",label:"Lub. Interval (hrs)",min:0,max:800,step:10},
    {key:"runtime_hours",label:"Runtime (hrs)",min:0,max:5000,step:50},
  ];

  return (
    <div className="grid-2">
      <div className="card">
        <div className="card-title">◉ Sensor Input</div>
        <div style={{marginBottom:14}}>
          <label>Equipment ID</label>
          <input value={form.equipment_id}
                 onChange={e=>setForm(f=>({...f,equipment_id:e.target.value.toUpperCase()}))} />
        </div>
        {FIELDS.map(f => (
          <div key={f.key} style={{marginBottom:12}}>
            <div style={{display:"flex",justifyContent:"space-between",marginBottom:5}}>
              <label style={{margin:0}}>{f.label}</label>
              <span style={{fontFamily:"var(--mono)",fontSize:13,color:"var(--amber)"}}>
                {form[f.key]}
              </span>
            </div>
            <input type="range" min={f.min} max={f.max} step={f.step}
                   value={form[f.key]}
                   onChange={e=>setForm(s=>({...s,[f.key]:parseFloat(e.target.value)}))} />
          </div>
        ))}
        <button className="btn btn-primary" style={{width:"100%",marginTop:8}} onClick={run} disabled={loading}>
          {loading ? <><span className="spinner"></span> Predicting...</> : "◉ Predict Failure"}
        </button>
      </div>

      {result && (
        <div>
          <div className="card section-gap">
            <div className="card-title">ML Prediction Result</div>
            <div style={{textAlign:"center",padding:"16px 0"}}>
              <div style={{fontSize:11,color:"var(--text-2)",marginBottom:8}}>HEALTH SCORE</div>
              <div style={{
                fontSize:64, fontFamily:"var(--mono)", fontWeight:500, lineHeight:1,
                color: result.health_score<40?"var(--red)":result.health_score<70?"var(--amber)":"var(--teal)"
              }}>
                {result.health_score}
              </div>
              <div style={{fontSize:13,color:"var(--text-2)"}}>/ 100</div>
              <div style={{marginTop:12}}>
                <span className={`badge badge-${result.risk_level?.toLowerCase()}`}>
                  {result.risk_level === "CRITICAL" && <span className="pulse-ring"></span>}
                  {result.risk_level}
                </span>
              </div>
            </div>
            <hr className="divider" />
            <div className="ml-grid">
              <div className="ml-stat">
                <div className="ml-stat-label">Failure Probability</div>
                <div className="ml-stat-val" style={{color:"var(--red)"}}>{(result.failure_probability*100).toFixed(0)}%</div>
              </div>
              <div className="ml-stat">
                <div className="ml-stat-label">RUL</div>
                <div className="ml-stat-val" style={{color:"var(--amber)"}}>{result.rul_days?.toFixed(0)} days</div>
              </div>
            </div>
            <div style={{marginTop:12,padding:"10px 14px",background:"var(--bg-2)",borderRadius:8,fontSize:12,color:"var(--text-1)",lineHeight:1.7}}>
              {result.recommendation}
            </div>
          </div>

          <div className="card">
            <div className="card-title">Top Risk Factors</div>
            {Object.entries(result.feature_contributions || {}).map(([k,v]) => (
              <div className="feature-bar" key={k}>
                <div className="feature-bar-header">
                  <span className="feature-bar-name">{k.replace(/_/g," ")}</span>
                  <span className="feature-bar-pct">{v}%</span>
                </div>
                <div className="feature-track">
                  <div className="feature-fill" style={{width:`${v}%`}} />
                </div>
              </div>
            ))}
            <div style={{marginTop:12,fontSize:12,color:"var(--text-2)"}}>
              Predicted failure: <span style={{color:"var(--amber)",fontFamily:"var(--mono)"}}>{result.predicted_failure_type}</span>
              {result.urgency_hours && <> · Act within <span style={{color:"var(--red)"}}>{result.urgency_hours}h</span></>}
            </div>
          </div>
        </div>
      )}
      {!result && (
        <div className="empty-state" style={{alignSelf:"center"}}>
          <div className="empty-icon">◉</div>
          <div>Adjust sensor sliders and run prediction</div>
        </div>
      )}
    </div>
  );
}

function Loading({ text }) {
  return (
    <div className="empty-state">
      <div className="spinner" style={{margin:"0 auto 12px"}}></div>
      <div>{text}</div>
    </div>
  );
}
