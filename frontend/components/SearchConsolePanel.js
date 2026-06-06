import { useState, useEffect, useRef, useCallback } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function gscFetch(path, token, options = {}) {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "API error");
  return data;
}

// ── Small UI atoms ─────────────────────────────────────────────────────────

function MetricCard({ label, value, sub, color = "#00d4ff" }) {
  return (
    <div className="rounded-xl p-4 flex flex-col gap-1"
      style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)" }}>
      <p className="text-xs uppercase tracking-widest font-semibold" style={{ color: "#4b5563" }}>{label}</p>
      <p className="text-2xl font-black" style={{ color }}>{value}</p>
      {sub && <p className="text-xs" style={{ color: "#4b5563" }}>{sub}</p>}
    </div>
  );
}

function Badge({ text, type = "blue" }) {
  const colors = {
    blue:   { bg: "rgba(0,212,255,0.1)",   border: "rgba(0,212,255,0.3)",   text: "#00d4ff" },
    green:  { bg: "rgba(34,197,94,0.1)",   border: "rgba(34,197,94,0.3)",   text: "#22c55e" },
    red:    { bg: "rgba(239,68,68,0.1)",   border: "rgba(239,68,68,0.3)",   text: "#ef4444" },
    orange: { bg: "rgba(249,115,22,0.1)",  border: "rgba(249,115,22,0.3)",  text: "#f97316" },
    yellow: { bg: "rgba(234,179,8,0.1)",   border: "rgba(234,179,8,0.3)",   text: "#eab308" },
  };
  const c = colors[type] || colors.blue;
  return (
    <span className="text-xs font-bold px-2 py-0.5 rounded-full"
      style={{ background: c.bg, border: `1px solid ${c.border}`, color: c.text }}>
      {text}
    </span>
  );
}

function ProgressBar({ pct }) {
  return (
    <div className="w-full h-2 rounded-full" style={{ background: "rgba(255,255,255,0.06)" }}>
      <div className="h-full rounded-full transition-all duration-500"
        style={{ width: `${pct}%`, background: "linear-gradient(90deg,#0066aa,#00d4ff)" }} />
    </div>
  );
}

function DataTable({ headers, rows, emptyMsg = "No data available." }) {
  if (!rows || rows.length === 0) {
    return <p className="text-sm py-3" style={{ color: "#4b5563" }}>{emptyMsg}</p>;
  }
  return (
    <div className="overflow-x-auto rounded-lg" style={{ border: "1px solid rgba(255,255,255,0.06)" }}>
      <table className="w-full text-xs">
        <thead>
          <tr style={{ background: "rgba(0,102,170,0.4)" }}>
            {headers.map((h, i) => (
              <th key={i} className="text-left px-3 py-2 font-semibold whitespace-nowrap"
                style={{ color: "#94a3b8", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} style={{ background: i % 2 === 0 ? "rgba(255,255,255,0.01)" : "transparent" }}>
              {row.map((cell, j) => (
                <td key={j} className="px-3 py-2 font-mono"
                  style={{ color: "#cbd5e1", borderBottom: "1px solid rgba(255,255,255,0.03)" }}>
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Setup guide (when not configured) ────────────────────────────────────────

function SetupGuide() {
  return (
    <div className="card space-y-4">
      <h3 className="text-lg font-bold" style={{ color: "#e2e8f0" }}>
        <span className="neon-cyan">◈</span> Setup Google Search Console Integration
      </h3>
      <p className="text-sm" style={{ color: "#94a3b8" }}>
        To connect Google Search Console, you need Google OAuth credentials.
        Follow these steps:
      </p>
      <ol className="space-y-3 text-sm" style={{ color: "#94a3b8" }}>
        {[
          ["Go to Google Cloud Console", "https://console.cloud.google.com/"],
          ["Create a new project (or select existing)"],
          ["Enable Search Console API", "APIs & Services → Library → Search Console API"],
          ["Create OAuth 2.0 credentials", "APIs & Services → Credentials → Create OAuth 2.0 Client ID"],
          ["Set application type to 'Web application'"],
          ["Add redirect URI", "http://localhost:8000/api/gsc/auth/callback"],
          ["Copy Client ID and Client Secret"],
          ["Add to backend/.env:", "GOOGLE_CLIENT_ID=your-client-id\nGOOGLE_CLIENT_SECRET=your-client-secret"],
          ["Restart the backend server"],
        ].map(([title, detail], i) => (
          <li key={i} className="flex gap-3">
            <span className="w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold"
              style={{ background: "rgba(0,102,170,0.3)", border: "1px solid rgba(0,212,255,0.3)", color: "#00d4ff" }}>
              {i + 1}
            </span>
            <div>
              <p className="font-medium" style={{ color: "#e2e8f0" }}>{title}</p>
              {detail && (
                <p className="text-xs mt-0.5 font-mono px-2 py-1 rounded" style={{ color: "#64748b", background: "rgba(255,255,255,0.03)" }}>
                  {detail}
                </p>
              )}
            </div>
          </li>
        ))}
      </ol>
      <div className="rounded-lg p-3 text-xs font-mono" style={{ background: "rgba(0,212,255,0.05)", border: "1px solid rgba(0,212,255,0.2)", color: "#64748b" }}>
        # backend/.env{"\n"}
        GOOGLE_CLIENT_ID=123456789-abc.apps.googleusercontent.com{"\n"}
        GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxx{"\n"}
        FRONTEND_URL=http://localhost:3000
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function SearchConsolePanel({ token }) {
  const [config, setConfig] = useState(null);           // {configured, redirect_uri}
  const [gscStatus, setGscStatus] = useState(null);     // {connected, properties}
  const [selectedProperty, setSelectedProperty] = useState("");
  const [reportStatus, setReportStatus] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [recentReports, setRecentReports] = useState([]);
  const [activeTab, setActiveTab] = useState("overview");
  const [mainTab, setMainTab] = useState("audit"); // "audit" | "keywords"
  const [keywordTrends, setKeywordTrends] = useState(null);
  const [kwLoading, setKwLoading] = useState(false);
  const [error, setError] = useState("");
  const [connecting, setConnecting] = useState(false);
  const pollRef = useRef(null);

  const stopPoll = () => { if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; } };

  // ── Lifecycle ───────────────────────────────────────────────────────────────

  const loadConfig = useCallback(async () => {
    try {
      const c = await gscFetch("/api/gsc/config", token);
      setConfig(c);
    } catch (_) {}
  }, [token]);

  const loadStatus = useCallback(async () => {
    try {
      const s = await gscFetch("/api/gsc/status", token);
      setGscStatus(s);
      if (s.connected && s.properties?.length > 0 && !selectedProperty) {
        setSelectedProperty(s.properties[0].url);
      }
    } catch (_) {}
  }, [token, selectedProperty]);

  const loadRecentReports = useCallback(async () => {
    try {
      const list = await gscFetch("/api/gsc/audit/list", token);
      setRecentReports(list);
      if (list.length > 0 && list[0].status === "completed" && !reportData) {
        loadReportResults(list[0].report_id);
      }
    } catch (_) {}
  }, [token]);

  useEffect(() => {
    if (!token) return;
    loadConfig();
    loadStatus();
    loadRecentReports();

    // Handle OAuth redirect back with ?gsc_connected=true
    const params = new URLSearchParams(window.location.search);
    if (params.get("gsc_connected") === "true") {
      window.history.replaceState({}, "", "/dashboard");
      loadStatus();
    }
    if (params.get("gsc_error")) {
      setError("Google OAuth failed. Please try again.");
      window.history.replaceState({}, "", "/dashboard");
    }
  }, [token]);

  // ── Actions ─────────────────────────────────────────────────────────────────

  const handleConnect = async () => {
    setConnecting(true);
    setError("");
    try {
      const data = await gscFetch("/api/gsc/auth/url", token);
      window.location.href = data.auth_url;
    } catch (e) {
      setError(e.message);
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm("Disconnect Google Search Console?")) return;
    try {
      await gscFetch("/api/gsc/disconnect", token, { method: "DELETE" });
      setGscStatus({ connected: false, properties: [] });
      setReportData(null);
      setReportStatus(null);
    } catch (e) {
      setError(e.message);
    }
  };

  const handleStartAudit = async () => {
    if (!selectedProperty) { setError("Select a property first."); return; }
    setError("");
    setReportData(null);
    try {
      const data = await gscFetch("/api/gsc/audit/start", token, {
        method: "POST",
        body: JSON.stringify({ property_url: selectedProperty }),
      });
      setReportStatus({ report_id: data.report_id, status: "running", progress: 0, progress_message: "Starting..." });
      startPoll(data.report_id);
    } catch (e) {
      setError(e.message);
    }
  };

  const startPoll = (reportId) => {
    stopPoll();
    pollRef.current = setInterval(async () => {
      try {
        const s = await gscFetch(`/api/gsc/audit/${reportId}/status`, token);
        setReportStatus(s);
        if (s.status === "completed") {
          stopPoll();
          loadReportResults(reportId);
          loadRecentReports();
        } else if (s.status === "failed") {
          stopPoll();
          setError("Audit failed: " + s.progress_message);
        }
      } catch (e) {
        stopPoll();
        setError(e.message);
      }
    }, 2500);
  };

  const loadReportResults = async (reportId) => {
    try {
      const data = await gscFetch(`/api/gsc/audit/${reportId}/results`, token);
      setReportData({ ...data, _report_id: reportId });
      setActiveTab("overview");
    } catch (_) {}
  };

  const loadKeywordTrends = async () => {
    if (!selectedProperty) { setError("Select a property first."); return; }
    setKwLoading(true);
    setError("");
    setKeywordTrends(null);
    try {
      const enc = encodeURIComponent(selectedProperty);
      const data = await gscFetch(`/api/gsc/keywords/trends?property_url=${enc}`, token);
      setKeywordTrends(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setKwLoading(false);
    }
  };

  const handleDownload = async (fmt) => {
    if (!reportData?._report_id) return;
    const rid = reportData._report_id;
    try {
      const res = await fetch(`${API}/api/gsc/audit/${rid}/download/${fmt}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) { setError("Download failed"); return; }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = fmt === "pdf" ? `GSC_Audit_${rid}.pdf` : `GSC_Reports_${rid}.zip`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError("Download error: " + e.message);
    }
  };

  // ── Render guards ────────────────────────────────────────────────────────────

  if (!config) return (
    <div className="card flex items-center justify-center py-12">
      <div className="animate-spin w-6 h-6 rounded-full" style={{ border: "2px solid rgba(0,212,255,0.2)", borderTopColor: "#00d4ff" }} />
    </div>
  );

  if (!config.configured) return <SetupGuide />;

  // ── Not connected state ──────────────────────────────────────────────────────

  if (!gscStatus?.connected) {
    return (
      <div className="card text-center py-12 space-y-5">
        <div className="w-16 h-16 mx-auto rounded-2xl flex items-center justify-center"
          style={{ background: "linear-gradient(135deg,#0066aa,#00d4ff)", boxShadow: "0 0 30px rgba(0,212,255,0.3)" }}>
          <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <div>
          <h3 className="text-xl font-bold" style={{ color: "#e2e8f0" }}>Connect Google Search Console</h3>
          <p className="text-sm mt-2" style={{ color: "#64748b" }}>
            See your real search performance — clicks, impressions, rankings, and opportunities.
          </p>
        </div>
        <div className="flex flex-wrap justify-center gap-3 text-xs" style={{ color: "#4b5563" }}>
          {["Clicks & Impressions", "Top Keywords", "CTR Analysis", "Declining Pages", "AI Insights", "DOCX + PDF Reports"].map(f => (
            <span key={f} className="flex items-center gap-1">
              <span style={{ color: "#22c55e" }}>✓</span> {f}
            </span>
          ))}
        </div>
        {error && <p className="text-sm" style={{ color: "#ef4444" }}>{error}</p>}
        <button onClick={handleConnect} disabled={connecting} className="btn-primary mx-auto flex items-center gap-2">
          {connecting ? (
            <><span className="animate-spin w-4 h-4 rounded-full" style={{ border: "2px solid rgba(255,255,255,0.3)", borderTopColor: "white" }} /> Redirecting to Google...</>
          ) : (
            <><svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"/></svg>
              Connect with Google</>
          )}
        </button>
      </div>
    );
  }

  // ── Connected — property selector ─────────────────────────────────────────

  const properties = gscStatus.properties || [];
  const isRunning  = reportStatus?.status === "running";

  return (
    <div className="space-y-4">

      {/* Header bar */}
      <div className="card space-y-3">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <span className="w-2 h-2 rounded-full" style={{ background: "#22c55e", boxShadow: "0 0 6px #22c55e" }} />
            <span className="text-sm font-semibold" style={{ color: "#22c55e" }}>Google Search Console Connected</span>
          </div>
          <div className="flex items-center gap-2">
            <select value={selectedProperty} onChange={e => { setSelectedProperty(e.target.value); setKeywordTrends(null); }}
              className="input-field text-sm py-1.5 px-3" style={{ minWidth: "220px" }}>
              {properties.map(p => <option key={p.url} value={p.url}>{p.url}</option>)}
              {properties.length === 0 && <option value="">No properties found</option>}
            </select>
            <button onClick={handleDisconnect} className="btn-secondary text-xs py-1.5 px-3">Disconnect</button>
          </div>
        </div>
        {/* Main tabs */}
        <div className="flex gap-1">
          {[
            { key: "audit",    label: "📋 SEO Audit" },
            { key: "keywords", label: "📈 Keyword Tracker" },
          ].map(t => (
            <button key={t.key} onClick={() => setMainTab(t.key)}
              className="px-4 py-2 text-sm font-medium rounded-lg transition-all"
              style={mainTab === t.key
                ? { background: "rgba(0,212,255,0.15)", color: "#00d4ff", border: "1px solid rgba(0,212,255,0.35)" }
                : { background: "rgba(255,255,255,0.03)", color: "#6b7280", border: "1px solid rgba(255,255,255,0.06)" }}>
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="rounded-lg px-4 py-3 text-sm" style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.25)", color: "#ef4444" }}>
          ⚠ {error}
        </div>
      )}

      {/* ── Keyword Tracker ── */}
      {mainTab === "keywords" && (
        <KeywordTrackerSection
          trends={keywordTrends}
          loading={kwLoading}
          onFetch={loadKeywordTrends}
          property={selectedProperty}
        />
      )}

      {/* ── Audit Section ── */}
      {mainTab === "audit" && <>

      {/* Progress */}
      {isRunning && reportStatus && (
        <div className="card space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span style={{ color: "#00d4ff" }}>⟳ {reportStatus.progress_message}</span>
            <span className="font-mono" style={{ color: "#4b5563" }}>{reportStatus.progress}%</span>
          </div>
          <ProgressBar pct={reportStatus.progress} />
          <div className="flex flex-wrap gap-1.5">
            {["Connecting","Queries","Pages","Trend","Devices","Analysis","AI Insights","Reports"].map((s, i) => (
              <span key={s} className="text-xs px-2 py-0.5 rounded-full"
                style={{
                  background: reportStatus.progress > i * 12 ? "rgba(0,212,255,0.15)" : "rgba(255,255,255,0.03)",
                  border: "1px solid " + (reportStatus.progress > i * 12 ? "rgba(0,212,255,0.4)" : "rgba(255,255,255,0.06)"),
                  color: reportStatus.progress > i * 12 ? "#00d4ff" : "#374151",
                }}>
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Recent reports picker */}
      {!reportData && !isRunning && recentReports.length > 0 && (
        <div className="card">
          <p className="text-xs font-semibold mb-3 uppercase tracking-widest" style={{ color: "#4b5563" }}>Recent Reports</p>
          <div className="space-y-1.5">
            {recentReports.slice(0, 5).map(r => (
              <div key={r.report_id}
                className="flex items-center justify-between p-2.5 rounded-lg cursor-pointer transition-all"
                style={{ border: "1px solid rgba(255,255,255,0.05)", background: "rgba(255,255,255,0.02)" }}
                onClick={() => r.status === "completed" && loadReportResults(r.report_id)}>
                <span className="text-sm font-mono truncate" style={{ color: "#94a3b8" }}>{r.property_url}</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs" style={{ color: "#4b5563" }}>{new Date(r.created_at).toLocaleDateString()}</span>
                  <Badge text={r.status} type={r.status === "completed" ? "green" : r.status === "running" ? "blue" : "red"} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      {reportData && <ReportView data={reportData} activeTab={activeTab} setActiveTab={setActiveTab} onDownload={handleDownload} />}

      {/* Audit action button */}
      {!isRunning && (
        <div className="flex justify-end">
          <button onClick={handleStartAudit} disabled={!selectedProperty}
            className="btn-primary text-sm py-2 px-5">
            ▶ Run Full Audit
          </button>
        </div>
      )}

      </> /* end audit section */}
    </div>
  );
}

// ── Report viewer ─────────────────────────────────────────────────────────────

function ReportView({ data, activeTab, setActiveTab, onDownload }) {
  const ov   = data.overview || {};
  const ai   = data.ai_insights || {};
  const tabs = [
    { key: "overview",      label: "📊 Overview" },
    { key: "queries",       label: "🔍 Queries" },
    { key: "pages",         label: "📄 Pages" },
    { key: "opportunities", label: "🚀 Opportunities" },
    { key: "declining",     label: "📉 Declining" },
    { key: "ai",            label: "🤖 AI Insights" },
    { key: "download",      label: "⬇ Download" },
  ];

  return (
    <div className="space-y-4">
      {/* Property + date range */}
      <div className="flex flex-wrap items-center gap-3 px-1">
        <span className="text-sm font-mono" style={{ color: "#00d4ff" }}>{data.property_url}</span>
        <span className="text-xs" style={{ color: "#4b5563" }}>{ov.date_range}</span>
      </div>

      {/* Tab nav */}
      <div className="flex gap-0.5 overflow-x-auto" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        {tabs.map(t => (
          <button key={t.key} onClick={() => setActiveTab(t.key)}
            className="px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors -mb-px"
            style={activeTab === t.key
              ? { borderColor: "#00d4ff", color: "#00d4ff" }
              : { borderColor: "transparent", color: "#6b7280" }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "overview"      && <OverviewTab ov={ov} devices={data.device_breakdown} />}
      {activeTab === "queries"       && <QueriesTab queries={data.top_queries} />}
      {activeTab === "pages"         && <PagesTab pages={data.top_pages} />}
      {activeTab === "opportunities" && <OpportunitiesTab opps={data.opportunities} ctrOpps={data.ctr_opportunities} />}
      {activeTab === "declining"     && <DecliningTab declining={data.declining_pages} period={data.period_comparison} />}
      {activeTab === "ai"            && <AIInsightsTab ai={ai} />}
      {activeTab === "download"      && <DownloadTab onDownload={onDownload} />}
    </div>
  );
}

// ── Tab: Overview ─────────────────────────────────────────────────────────────

function OverviewTab({ ov, devices }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <MetricCard label="Total Clicks"      value={ov.clicks?.toLocaleString() || "0"} sub="last 28 days" />
        <MetricCard label="Total Impressions" value={ov.impressions?.toLocaleString() || "0"} sub="last 28 days" color="#818cf8" />
        <MetricCard label="Avg CTR"           value={`${ov.ctr || 0}%`} sub="click-through rate" color="#22c55e" />
        <MetricCard label="Avg Position"      value={ov.position || "0"} sub="search ranking" color="#f97316" />
      </div>
      {devices && devices.length > 0 && (
        <div className="card">
          <p className="text-sm font-semibold mb-3" style={{ color: "#e2e8f0" }}>Device Breakdown</p>
          <DataTable
            headers={["Device", "Clicks", "Impressions", "CTR %", "Avg Position"]}
            rows={devices.map(d => [
              d.device.charAt(0).toUpperCase() + d.device.slice(1),
              d.clicks.toLocaleString(), d.impressions.toLocaleString(),
              `${d.ctr}%`, d.position,
            ])}
          />
        </div>
      )}
    </div>
  );
}

// ── Tab: Queries ──────────────────────────────────────────────────────────────

function QueriesTab({ queries }) {
  const [search, setSearch] = useState("");
  const filtered = (queries || []).filter(q => q.query.toLowerCase().includes(search.toLowerCase()));
  return (
    <div className="card space-y-3">
      <div className="flex items-center gap-3">
        <p className="text-sm font-semibold" style={{ color: "#e2e8f0" }}>Top Search Queries</p>
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Filter queries..."
          className="input-field text-xs py-1.5 px-3 flex-1 max-w-xs" />
      </div>
      <DataTable
        headers={["Query", "Clicks", "Impressions", "CTR %", "Avg Position"]}
        rows={filtered.map(q => [
          q.query, q.clicks.toLocaleString(), q.impressions.toLocaleString(),
          `${q.ctr}%`, q.position,
        ])}
        emptyMsg="No queries found."
      />
    </div>
  );
}

// ── Tab: Pages ────────────────────────────────────────────────────────────────

function PagesTab({ pages }) {
  const [search, setSearch] = useState("");
  const filtered = (pages || []).filter(p => p.page.toLowerCase().includes(search.toLowerCase()));
  return (
    <div className="card space-y-3">
      <div className="flex items-center gap-3">
        <p className="text-sm font-semibold" style={{ color: "#e2e8f0" }}>Top Pages</p>
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Filter pages..."
          className="input-field text-xs py-1.5 px-3 flex-1 max-w-sm" />
      </div>
      <DataTable
        headers={["Page URL", "Clicks", "Impressions", "CTR %", "Avg Position"]}
        rows={filtered.map(p => [
          <span key={p.page} className="font-mono text-xs truncate block max-w-xs" title={p.page}>{p.page}</span>,
          p.clicks.toLocaleString(), p.impressions.toLocaleString(),
          `${p.ctr}%`, p.position,
        ])}
        emptyMsg="No pages found."
      />
    </div>
  );
}

// ── Tab: Opportunities ────────────────────────────────────────────────────────

function OpportunitiesTab({ opps, ctrOpps }) {
  const totalPotential   = (opps || []).reduce((s, o) => s + (o.potential_clicks || 0), 0);
  const totalCtrPotential = (ctrOpps || []).reduce((s, o) => s + (o.potential_extra_clicks || 0), 0);

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="grid grid-cols-2 gap-3">
        <MetricCard label="Page 2 Keywords" value={(opps || []).length} sub={`+${totalPotential.toLocaleString()} potential clicks`} color="#f97316" />
        <MetricCard label="CTR Opportunities" value={(ctrOpps || []).length} sub={`+${totalCtrPotential.toLocaleString()} potential clicks`} color="#818cf8" />
      </div>

      {/* Page 2 opportunities */}
      <div className="card space-y-3">
        <div>
          <p className="text-sm font-semibold" style={{ color: "#e2e8f0" }}>Page 2 Keywords — Push to Page 1</p>
          <p className="text-xs mt-1" style={{ color: "#4b5563" }}>Queries ranking 11–30 with high impressions. Content optimization can push these to page 1.</p>
        </div>
        <DataTable
          headers={["Query", "Position", "Impressions/mo", "+Potential Clicks", "Priority"]}
          rows={(opps || []).map(o => [
            o.query,
            <span key={o.query} style={{ color: "#f97316" }}>{o.current_position}</span>,
            o.impressions.toLocaleString(),
            <span key={o.query+"c"} style={{ color: "#22c55e" }}>+{o.potential_clicks}</span>,
            <Badge key={o.query+"p"} text={o.priority.toUpperCase()} type={o.priority === "high" ? "red" : "orange"} />,
          ])}
          emptyMsg="No page-2 opportunities found."
        />
      </div>

      {/* CTR opportunities */}
      <div className="card space-y-3">
        <div>
          <p className="text-sm font-semibold" style={{ color: "#e2e8f0" }}>CTR Improvement — Rewrite Title & Meta</p>
          <p className="text-xs mt-1" style={{ color: "#4b5563" }}>Pages getting impressions but below-expected click-through rates.</p>
        </div>
        <DataTable
          headers={["Page", "Impressions/mo", "Actual CTR%", "Expected CTR%", "+Extra Clicks"]}
          rows={(ctrOpps || []).map(o => [
            <span key={o.page} className="font-mono text-xs truncate block max-w-xs" title={o.page}>{o.page}</span>,
            o.impressions.toLocaleString(),
            <span key={o.page+"a"} style={{ color: "#ef4444" }}>{o.actual_ctr}%</span>,
            <span key={o.page+"e"} style={{ color: "#22c55e" }}>{o.expected_ctr}%</span>,
            <span key={o.page+"c"} style={{ color: "#22c55e" }}>+{o.potential_extra_clicks}</span>,
          ])}
          emptyMsg="No significant CTR gaps found."
        />
      </div>
    </div>
  );
}

// ── Tab: Declining ────────────────────────────────────────────────────────────

function DecliningTab({ declining, period }) {
  if (!declining || declining.length === 0) {
    return (
      <div className="card text-center py-10">
        <p className="text-2xl mb-2">📈</p>
        <p className="text-sm font-semibold" style={{ color: "#22c55e" }}>No significant traffic declines detected</p>
        <p className="text-xs mt-1" style={{ color: "#4b5563" }}>
          {period?.current_period && `Compared: ${period.current_period} vs ${period.previous_period}`}
        </p>
      </div>
    );
  }
  return (
    <div className="card space-y-3">
      <div>
        <p className="text-sm font-semibold" style={{ color: "#e2e8f0" }}>Pages Losing Traffic</p>
        {period && (
          <p className="text-xs mt-1" style={{ color: "#4b5563" }}>
            Current: {period.current_period} vs Previous: {period.previous_period}
          </p>
        )}
      </div>
      <DataTable
        headers={["Page", "Now", "Before", "Change", "% Change", "Position Δ", "Severity"]}
        rows={declining.map(d => [
          <span key={d.page} className="font-mono text-xs truncate block max-w-xs" title={d.page}>{d.page}</span>,
          d.current_clicks, d.previous_clicks,
          <span key={d.page+"c"} style={{ color: "#ef4444" }}>{d.click_change}</span>,
          <span key={d.page+"p"} style={{ color: "#ef4444" }}>{d.pct_change}%</span>,
          <span key={d.page+"pos"} style={{ color: d.position_change > 0 ? "#ef4444" : "#22c55e" }}>
            {d.position_change > 0 ? "+" : ""}{d.position_change}
          </span>,
          <Badge key={d.page+"s"} text={d.severity.toUpperCase()}
            type={d.severity === "critical" ? "red" : d.severity === "high" ? "orange" : "yellow"} />,
        ])}
      />
    </div>
  );
}

// ── Tab: AI Insights ──────────────────────────────────────────────────────────

function AIInsightsTab({ ai }) {
  if (!ai || ai.error) {
    return (
      <div className="card py-8 text-center">
        <p className="text-sm" style={{ color: "#4b5563" }}>
          {ai?.error || "AI insights not available for this report."}
        </p>
      </div>
    );
  }
  return (
    <div className="space-y-4">
      {/* Health */}
      {ai.health_assessment && (
        <div className="card">
          <p className="text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: "#4b5563" }}>Search Health Assessment</p>
          <p className="text-sm leading-relaxed" style={{ color: "#e2e8f0" }}>{ai.health_assessment}</p>
        </div>
      )}

      {/* Priority actions */}
      {ai.top_priority_actions?.length > 0 && (
        <div className="card space-y-3">
          <p className="text-sm font-semibold" style={{ color: "#e2e8f0" }}>Priority Actions</p>
          {ai.top_priority_actions.map((a, i) => (
            <div key={i} className="rounded-lg p-3 space-y-1"
              style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div className="flex items-center gap-2">
                <Badge text={a.impact?.toUpperCase()} type={a.impact === "high" ? "red" : a.impact === "medium" ? "orange" : "blue"} />
                <Badge text={a.effort} type="blue" />
                <span className="text-sm font-medium" style={{ color: "#e2e8f0" }}>{a.action}</span>
              </div>
              {a.why && <p className="text-xs" style={{ color: "#64748b" }}>→ {a.why}</p>}
            </div>
          ))}
        </div>
      )}

      {/* Quick wins */}
      {ai.quick_wins?.length > 0 && (
        <div className="card space-y-2">
          <p className="text-sm font-semibold" style={{ color: "#e2e8f0" }}>Quick Wins</p>
          {ai.quick_wins.map((w, i) => (
            <div key={i} className="flex gap-2 text-sm">
              <span style={{ color: "#22c55e" }}>✓</span>
              <span style={{ color: "#94a3b8" }}>{w}</span>
            </div>
          ))}
        </div>
      )}

      {/* Recovery + CTR tips */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {ai.traffic_recovery && (
          <div className="card">
            <p className="text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: "#4b5563" }}>Traffic Recovery</p>
            <p className="text-sm leading-relaxed" style={{ color: "#94a3b8" }}>{ai.traffic_recovery}</p>
          </div>
        )}
        {ai.ctr_improvement_tips && (
          <div className="card">
            <p className="text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: "#4b5563" }}>CTR Improvement</p>
            <p className="text-sm leading-relaxed" style={{ color: "#94a3b8" }}>{ai.ctr_improvement_tips}</p>
          </div>
        )}
      </div>

      {/* Content plan */}
      {ai.content_plan && (
        <div className="card">
          <p className="text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: "#4b5563" }}>Content Plan</p>
          <p className="text-sm leading-relaxed" style={{ color: "#94a3b8" }}>{ai.content_plan}</p>
        </div>
      )}

      {/* Estimated impact */}
      {ai.estimated_monthly_clicks && (
        <div className="rounded-xl p-4" style={{ background: "rgba(0,212,255,0.05)", border: "1px solid rgba(0,212,255,0.2)" }}>
          <p className="text-xs font-semibold uppercase tracking-widest mb-1" style={{ color: "#00d4ff" }}>Estimated Monthly Clicks</p>
          <p className="text-sm" style={{ color: "#e2e8f0" }}>{ai.estimated_monthly_clicks}</p>
        </div>
      )}
    </div>
  );
}

// ── Keyword Tracker Section ───────────────────────────────────────────────────

const TREND_CONFIG = {
  rising:  { label: "↑ Rising",  color: "#22c55e", bg: "rgba(34,197,94,0.12)",  border: "rgba(34,197,94,0.3)" },
  falling: { label: "↓ Falling", color: "#ef4444", bg: "rgba(239,68,68,0.12)",  border: "rgba(239,68,68,0.3)" },
  new:     { label: "★ New",     color: "#00d4ff", bg: "rgba(0,212,255,0.12)",  border: "rgba(0,212,255,0.3)" },
  lost:    { label: "✕ Lost",    color: "#f97316", bg: "rgba(249,115,22,0.12)", border: "rgba(249,115,22,0.3)" },
  stable:  { label: "→ Stable",  color: "#6b7280", bg: "rgba(107,114,128,0.08)",border: "rgba(107,114,128,0.2)" },
};

function TrendBadge({ trend }) {
  const cfg = TREND_CONFIG[trend] || TREND_CONFIG.stable;
  return (
    <span className="text-xs font-semibold px-2 py-0.5 rounded-full whitespace-nowrap"
      style={{ color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.border}` }}>
      {cfg.label}
    </span>
  );
}

function KeywordTrackerSection({ trends, loading, onFetch, property }) {
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState("impressions");

  const summary = trends?.summary || {};
  const allKw   = trends?.keywords || [];

  const filtered = allKw
    .filter(k => filter === "all" || k.trend === filter)
    .filter(k => k.query.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      if (sortBy === "impressions") return (b.impressions || 0) - (a.impressions || 0);
      if (sortBy === "position")   return (a.current_position || 99) - (b.current_position || 99);
      if (sortBy === "change")     return (b.position_change || 0) - (a.position_change || 0);
      if (sortBy === "clicks")     return (b.clicks || 0) - (a.clicks || 0);
      return 0;
    });

  const filterTabs = [
    { key: "all",     label: "All",     count: summary.total   || 0 },
    { key: "rising",  label: "Rising",  count: summary.rising  || 0 },
    { key: "falling", label: "Falling", count: summary.falling || 0 },
    { key: "new",     label: "New",     count: summary.new     || 0 },
    { key: "lost",    label: "Lost",    count: summary.lost    || 0 },
    { key: "stable",  label: "Stable",  count: summary.stable  || 0 },
  ];

  if (!trends && !loading) {
    return (
      <div className="card text-center py-12 space-y-4">
        <p className="text-4xl">📈</p>
        <div>
          <p className="text-lg font-bold" style={{ color: "#e2e8f0" }}>Keyword Rank Tracker</p>
          <p className="text-sm mt-2" style={{ color: "#4b5563" }}>
            Compare keyword positions: current 28 days vs previous 28 days.
            See which keywords are rising, falling, or newly appearing.
          </p>
        </div>
        {property ? (
          <button onClick={onFetch} className="btn-primary mx-auto flex items-center gap-2">
            📈 Fetch Keyword Trends
          </button>
        ) : (
          <p className="text-sm" style={{ color: "#ef4444" }}>Select a property first.</p>
        )}
      </div>
    );
  }

  if (loading) {
    return (
      <div className="card flex flex-col items-center justify-center py-12 gap-4">
        <div className="animate-spin w-8 h-8 rounded-full"
          style={{ border: "2px solid rgba(0,212,255,0.2)", borderTopColor: "#00d4ff" }} />
        <p className="text-sm" style={{ color: "#4b5563" }}>Fetching keyword trends from Google Search Console...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {[
          { label: "Rising",  val: summary.rising  || 0, color: "#22c55e" },
          { label: "Falling", val: summary.falling || 0, color: "#ef4444" },
          { label: "New",     val: summary.new     || 0, color: "#00d4ff" },
          { label: "Lost",    val: summary.lost    || 0, color: "#f97316" },
          { label: "Stable",  val: summary.stable  || 0, color: "#6b7280" },
        ].map(c => (
          <div key={c.label} className="rounded-xl p-4 text-center"
            style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)" }}>
            <p className="text-2xl font-black" style={{ color: c.color }}>{c.val}</p>
            <p className="text-xs mt-1 uppercase tracking-widest font-semibold" style={{ color: "#4b5563" }}>{c.label}</p>
          </div>
        ))}
      </div>

      {/* Period info */}
      {trends && (
        <div className="flex flex-wrap gap-4 text-xs px-1" style={{ color: "#4b5563" }}>
          <span>Current: <span style={{ color: "#94a3b8" }}>{trends.current_period}</span></span>
          <span>vs Previous: <span style={{ color: "#94a3b8" }}>{trends.previous_period}</span></span>
          <span style={{ color: "#4b5563" }}>· Position improvement = ↑ Rise (moved up in rankings)</span>
        </div>
      )}

      {/* Filter + Search + Refresh */}
      <div className="card space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex gap-1 flex-wrap">
            {filterTabs.map(t => (
              <button key={t.key} onClick={() => setFilter(t.key)}
                className="text-xs px-3 py-1.5 rounded-lg font-medium transition-all"
                style={filter === t.key
                  ? { background: "rgba(0,212,255,0.15)", color: "#00d4ff", border: "1px solid rgba(0,212,255,0.35)" }
                  : { background: "rgba(255,255,255,0.03)", color: "#6b7280", border: "1px solid rgba(255,255,255,0.06)" }}>
                {t.label} <span className="ml-1 opacity-60">({t.count})</span>
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <input value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Search keywords..." className="input-field text-xs py-1.5 px-3"
              style={{ minWidth: "180px" }} />
            <select value={sortBy} onChange={e => setSortBy(e.target.value)}
              className="input-field text-xs py-1.5 px-3">
              <option value="impressions">Sort: Impressions</option>
              <option value="clicks">Sort: Clicks</option>
              <option value="position">Sort: Position</option>
              <option value="change">Sort: Position Change</option>
            </select>
            <button onClick={onFetch}
              className="text-xs px-3 py-1.5 rounded-lg font-medium"
              style={{ background: "rgba(255,255,255,0.05)", color: "#94a3b8", border: "1px solid rgba(255,255,255,0.08)" }}>
              ↻ Refresh
            </button>
          </div>
        </div>

        {/* Table */}
        {filtered.length === 0 ? (
          <p className="text-sm text-center py-6" style={{ color: "#4b5563" }}>No keywords found for this filter.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                  {["Keyword", "Trend", "Current Pos", "Prev Pos", "Pos Change", "Clicks", "Impressions", "CTR"].map(h => (
                    <th key={h} className="text-left py-2 px-3 font-semibold uppercase tracking-wide"
                      style={{ color: "#4b5563" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.slice(0, 100).map((k, i) => (
                  <tr key={k.query + i}
                    style={{ borderBottom: "1px solid rgba(255,255,255,0.03)" }}
                    className="transition-colors hover:bg-white hover:bg-opacity-5">
                    <td className="py-2.5 px-3 font-mono" style={{ color: "#e2e8f0", maxWidth: "220px" }}>
                      <span className="truncate block" title={k.query}>{k.query}</span>
                    </td>
                    <td className="py-2.5 px-3"><TrendBadge trend={k.trend} /></td>
                    <td className="py-2.5 px-3 text-center font-bold" style={{ color: "#e2e8f0" }}>
                      {k.current_position ?? "—"}
                    </td>
                    <td className="py-2.5 px-3 text-center" style={{ color: "#6b7280" }}>
                      {k.previous_position ?? "—"}
                    </td>
                    <td className="py-2.5 px-3 text-center font-bold">
                      {k.position_change == null ? "—" : (
                        <span style={{ color: k.position_change > 0 ? "#22c55e" : k.position_change < 0 ? "#ef4444" : "#6b7280" }}>
                          {k.position_change > 0 ? "+" : ""}{k.position_change}
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-center" style={{ color: "#94a3b8" }}>{k.clicks ?? 0}</td>
                    <td className="py-2.5 px-3 text-center" style={{ color: "#94a3b8" }}>{(k.impressions ?? 0).toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-center" style={{ color: "#94a3b8" }}>{k.ctr ?? 0}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filtered.length > 100 && (
              <p className="text-center text-xs py-3" style={{ color: "#4b5563" }}>
                Showing 100 of {filtered.length} keywords
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Tab: Download ─────────────────────────────────────────────────────────────

function DownloadTab({ onDownload }) {
  return (
    <div className="card space-y-4">
      <p className="text-sm font-semibold" style={{ color: "#e2e8f0" }}>Download Reports</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {[
          {
            title: "DOCX Reports (ZIP)",
            desc: "3 Word documents: Full Audit, Traffic Loss, Keyword Opportunities",
            icon: "📄", fmt: "docx", color: "#0066aa",
          },
          {
            title: "PDF Report",
            desc: "Professional single-page PDF with all data and AI insights",
            icon: "📋", fmt: "pdf", color: "#dc2626",
          },
        ].map(r => (
          <button key={r.fmt} onClick={() => onDownload(r.fmt)}
            className="p-4 rounded-xl text-left transition-all"
            style={{ border: `1px solid rgba(255,255,255,0.08)`, background: "rgba(255,255,255,0.02)" }}
            onMouseEnter={e => e.currentTarget.style.background = "rgba(0,212,255,0.04)"}
            onMouseLeave={e => e.currentTarget.style.background = "rgba(255,255,255,0.02)"}>
            <p className="text-xl mb-2">{r.icon}</p>
            <p className="text-sm font-semibold" style={{ color: "#e2e8f0" }}>{r.title}</p>
            <p className="text-xs mt-1" style={{ color: "#4b5563" }}>{r.desc}</p>
          </button>
        ))}
      </div>
      <div className="rounded-lg p-3 text-xs" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)", color: "#4b5563" }}>
        Reports include: Performance Overview · Top Queries · Top Pages · Declining Pages · Keyword Opportunities · CTR Gaps · AI Recommendations
      </div>
    </div>
  );
}
