import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/router";
import VoiceInput from "../components/VoiceInput";
import AuditProgress from "../components/AuditProgress";
import ReportViewer from "../components/ReportViewer";
import CompetitorPanel from "../components/CompetitorPanel";
import SearchConsolePanel from "../components/SearchConsolePanel";
import ToolsPanel from "../components/ToolsPanel";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const AUDIT_TYPES = [
  { key: "full", label: "Full SEO Audit", icon: "🔍", desc: "Complete technical + on-page audit" },
  { key: "technical", label: "Technical SEO", icon: "⚙️", desc: "Crawl errors, robots, sitemap, schema" },
  { key: "onpage", label: "On-Page SEO", icon: "📄", desc: "Title, meta, H1, content analysis" },
  { key: "product", label: "Product Page SEO", icon: "🛒", desc: "E-commerce product page audit" },
  { key: "category", label: "Category Page SEO", icon: "📂", desc: "Category / collection page audit" },
  { key: "blog", label: "Blog SEO Plan", icon: "✍️", desc: "Blog/article SEO recommendations" },
  { key: "tracking", label: "GTM / GA4 / Pixel", icon: "📊", desc: "Analytics tracking setup guide" },
];

function useAuth() {
  const router = useRouter();
  const [token, setToken] = useState(null);
  const [username, setUsername] = useState("");

  useEffect(() => {
    const t = localStorage.getItem("token");
    const u = localStorage.getItem("username");
    if (!t) { router.push("/"); return; }
    setToken(t);
    setUsername(u || "User");
  }, []);

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    router.push("/");
  };

  return { token, username, logout };
}

async function apiFetch(path, token, options = {}) {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json", ...options.headers },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "API error");
  return data;
}

export default function Dashboard() {
  const { token, username, logout } = useAuth();
  const router = useRouter();

  const [url, setUrl] = useState("");
  const [selectedType, setSelectedType] = useState("full");
  const [textCommand, setTextCommand] = useState("");

  const [currentAudit, setCurrentAudit] = useState(null);
  const [auditStatus, setAuditStatus] = useState(null);
  const [auditResults, setAuditResults] = useState(null);
  const [auditHistory, setAuditHistory] = useState([]);
  const [reportFiles, setReportFiles] = useState([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("audit"); // audit | results | history | competitor | gsc | benchmarks

  const [benchmarks, setBenchmarks] = useState(null);
  const [benchmarkUrl, setBenchmarkUrl] = useState("");
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);

  const pollRef = useRef(null);

  const loadHistory = useCallback(async () => {
    if (!token) return;
    try {
      const data = await apiFetch("/api/audit/list", token);
      setAuditHistory(data);
    } catch (_) {}
  }, [token]);

  useEffect(() => {
    if (token) loadHistory();
  }, [token, loadHistory]);

  const stopPolling = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  };

  const startPolling = (auditId) => {
    stopPolling();
    pollRef.current = setInterval(async () => {
      try {
        const status = await apiFetch(`/api/audit/${auditId}/status`, token);
        setAuditStatus(status);
        if (status.status === "completed") {
          stopPolling();
          loadHistory();
          fetchResults(auditId);
        } else if (status.status === "failed") {
          stopPolling();
          setError("Audit failed: " + status.progress_message);
        }
      } catch (e) {
        setError(e.message);
        stopPolling();
      }
    }, 2000);
  };

  const fetchResults = async (auditId) => {
    try {
      const results = await apiFetch(`/api/audit/${auditId}/results`, token);
      setAuditResults(results);
      setActiveTab("results");

      const files = await apiFetch(`/api/reports/${auditId}/files`, token);
      setReportFiles(files.files || []);
    } catch (e) {
      setError(e.message);
    }
  };

  const handleStartAudit = async () => {
    if (!url.trim()) { setError("Please enter a website URL"); return; }
    if (!url.startsWith("http")) { setError("URL must start with http:// or https://"); return; }

    setLoading(true);
    setError("");
    setAuditResults(null);
    setReportFiles([]);
    setAuditStatus(null);

    try {
      const data = await apiFetch("/api/audit/start", token, {
        method: "POST",
        body: JSON.stringify({ url: url.trim(), audit_type: selectedType }),
      });
      setCurrentAudit(data);
      setActiveTab("audit");
      startPolling(data.audit_id);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const parseCommand = (text) => {
    const lower = text.toLowerCase().trim();
    const result = { type: null, url: null, autoStart: false };

    // --- Detect audit type ---
    if (/\b(gtm|ga4|pixel|tag\s*manager|analytics|tracking|facebook\s*pixel)\b/.test(lower))
      result.type = "tracking";
    else if (/\b(technical\s*seo|technical audit|crawl|sitemap|robots|canonical)\b/.test(lower))
      result.type = "technical";
    else if (/\b(product\s*page|product\s*seo|listing\s*page)\b/.test(lower))
      result.type = "product";
    else if (/\b(category\s*page|category\s*seo|collection\s*page)\b/.test(lower))
      result.type = "category";
    else if (/\b(blog\s*seo|blog\s*plan|article\s*seo|content\s*seo)\b/.test(lower))
      result.type = "blog";
    else if (/\b(on[\s-]?page\s*seo|on[\s-]?page audit|meta|title|h1|heading)\b/.test(lower))
      result.type = "onpage";
    else if (/\b(full\s*audit|complete\s*audit|full\s*seo|seo\s*audit)\b/.test(lower))
      result.type = "full";

    // --- Extract URL (http/https or bare domain) ---
    const httpMatch = text.match(/https?:\/\/[^\s,]+/);
    if (httpMatch) {
      result.url = httpMatch[0].replace(/[.,;!?]$/, "");
    } else {
      const domainMatch = text.match(/\b(www\.)?[\w-]+\.(in|com|org|net|co|io|ai|pk|us|uk)[^\s]*/i);
      if (domainMatch) result.url = "https://" + domainMatch[0].replace(/^www\./, "www.");
    }

    // --- Auto-start if command has action words ---
    if (/\b(run|start|check|audit|analyse|analyze|do|perform|get|show|scan)\b/.test(lower))
      result.autoStart = true;

    return result;
  };

  const handleVoiceCommand = (transcript) => {
    setTextCommand(transcript);
    const parsed = parseCommand(transcript);

    if (parsed.type) setSelectedType(parsed.type);
    if (parsed.url) setUrl(parsed.url);

    const typeLabel = parsed.type || selectedType;
    const targetUrl = parsed.url || url;
    speak(`Got it. ${typeLabel} audit for ${targetUrl || "the website"}`);

    if (parsed.autoStart && (parsed.url || url)) {
      setTimeout(() => handleStartAudit(), 600);
    }
  };

  const speak = (text) => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(text);
      utter.rate = 1.0;
      window.speechSynthesis.speak(utter);
    }
  };

  const handleTextCommand = () => {
    if (!textCommand.trim()) return;
    const parsed = parseCommand(textCommand);
    if (parsed.type) setSelectedType(parsed.type);
    if (parsed.url) setUrl(parsed.url);

    if (parsed.autoStart && (parsed.url || url)) {
      setTimeout(() => handleStartAudit(), 300);
    } else if (!parsed.autoStart) {
      // Show feedback what was parsed
      if (parsed.type || parsed.url) {
        setError("");
      }
    }
  };

  const handleDownloadZip = () => {
    if (!currentAudit) return;
    window.open(`${API}/api/reports/${currentAudit.audit_id}/download?token=${token}`, "_blank");
    // Use proper auth header approach
    fetch(`${API}/api/reports/${currentAudit.audit_id}/download`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `SEO_Audit_${currentAudit.audit_id}.zip`;
        a.click();
        URL.revokeObjectURL(url);
      })
      .catch(() => setError("Download failed"));
  };

  const loadBenchmarks = async (filterUrl) => {
    setBenchmarkLoading(true);
    try {
      const qs = filterUrl ? `?url=${encodeURIComponent(filterUrl)}` : "";
      const data = await apiFetch(`/api/audit/benchmarks${qs}`, token);
      setBenchmarks(data);
      if (!filterUrl && data.available_urls?.length) setBenchmarkUrl(data.available_urls[0]);
    } catch (e) {
      setError(e.message);
    } finally {
      setBenchmarkLoading(false);
    }
  };

  const handleLoadHistoryAudit = async (audit) => {
    setCurrentAudit({ audit_id: audit.audit_id });
    setAuditStatus(audit);
    if (audit.status === "completed") {
      await fetchResults(audit.audit_id);
    } else if (audit.status === "running") {
      startPolling(audit.audit_id);
      setActiveTab("audit");
    }
  };

  if (!token) return <div className="min-h-screen flex items-center justify-center">Loading...</div>;

  const isRunning = auditStatus?.status === "running";
  const isCompleted = auditStatus?.status === "completed";

  // Live command preview
  const cmdPreview = textCommand.trim() ? parseCommand(textCommand) : null;

  return (
    <div className="min-h-screen grid-bg">
      {/* Navbar */}
      <nav style={{ background: "rgba(3,7,18,0.9)", borderBottom: "1px solid rgba(0,212,255,0.12)", backdropFilter: "blur(20px)" }}
        className="sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center"
              style={{ background: "linear-gradient(135deg,#0066aa,#00d4ff)", boxShadow: "0 0 20px rgba(0,212,255,0.4)" }}>
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div>
              <span className="font-black text-white text-lg tracking-tight neon-cyan">SEO AI Agent</span>
              <span className="ml-2 text-xs px-1.5 py-0.5 rounded font-mono" style={{ color:"#00d4ff", border:"1px solid rgba(0,212,255,0.3)", background:"rgba(0,212,255,0.08)" }}>v2047</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm" style={{ color:"#64748b" }}>
              <span style={{ color:"#00d4ff" }}>▸</span> {username}
            </span>
            <button onClick={logout} className="btn-secondary text-sm py-1.5 px-3">Logout</button>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">

        {/* Input Section */}
        <div className="card card-glow-cyan">
          <h2 className="text-xl font-bold mb-5 flex items-center gap-2" style={{ color:"#e2e8f0" }}>
            <span className="neon-cyan">◈</span>
            <span>Website SEO Analyzer</span>
            <span className="text-xs font-mono ml-2" style={{ color:"#4b5563" }}>// powered by Claude AI + Google PageSpeed</span>
          </h2>

          {/* URL Input */}
          <div className="flex gap-3 mb-4">
            <input type="url" value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleStartAudit()}
              className="input-field flex-1 text-base font-mono"
              placeholder="https://yourwebsite.com"
              disabled={isRunning} />
            <button onClick={handleStartAudit} disabled={loading || isRunning} className="btn-primary whitespace-nowrap">
              {loading || isRunning ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                  </svg>
                  Scanning...
                </span>
              ) : "▶ Run Audit"}
            </button>
          </div>

          {/* Text / Voice Command */}
          <div className="mb-5">
            <div className="flex gap-2">
              <input type="text" value={textCommand}
                onChange={(e) => setTextCommand(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleTextCommand()}
                className="input-field flex-1 text-sm"
                placeholder='AI command: "run technical seo bechdu.in" or "on-page audit cashify.in"'
                disabled={isRunning} />
              <button onClick={handleTextCommand} disabled={isRunning} className="btn-secondary text-sm py-2 px-3">Run</button>
              <VoiceInput onTranscript={handleVoiceCommand} disabled={isRunning} />
            </div>

            {cmdPreview && (cmdPreview.type || cmdPreview.url) && (
              <div className="mt-2 flex items-center gap-3 text-xs px-3 py-2 rounded-lg"
                style={{ background:"rgba(0,212,255,0.06)", border:"1px solid rgba(0,212,255,0.2)" }}>
                <span style={{ color:"#00d4ff" }} className="font-mono font-semibold">› detected:</span>
                {cmdPreview.type && <span className="badge-blue">{AUDIT_TYPES.find(t => t.key === cmdPreview.type)?.icon} {cmdPreview.type}</span>}
                {cmdPreview.url && <span className="font-medium" style={{ color:"#00ff88" }}>◎ {cmdPreview.url}</span>}
                {cmdPreview.autoStart && <span style={{ color:"#ffbb00" }} className="font-medium">⚡ auto-start</span>}
                {!cmdPreview.autoStart && <span style={{ color:"#374151" }}>— press Run to apply</span>}
              </div>
            )}

            <div className="mt-2 flex flex-wrap gap-1.5">
              {["on page seo cashify.in","technical audit bechdu.in","run product seo https://bechdu.in","gtm guide"].map((ex) => (
                <button key={ex}
                  onClick={() => { setTextCommand(ex); const p = parseCommand(ex); if(p.type) setSelectedType(p.type); if(p.url) setUrl(p.url); }}
                  className="text-xs px-2.5 py-1 rounded-full transition-colors font-mono"
                  style={{ background:"rgba(255,255,255,0.04)", border:"1px solid rgba(255,255,255,0.08)", color:"#6b7280" }}>
                  {ex}
                </button>
              ))}
            </div>
          </div>

          {/* Audit Type Grid */}
          <div>
            <p className="text-xs font-semibold mb-3 uppercase tracking-widest" style={{ color:"#4b5563" }}>Select Audit Type</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
              {AUDIT_TYPES.map((type) => (
                <button key={type.key} onClick={() => setSelectedType(type.key)} disabled={isRunning}
                  className="flex flex-col items-start p-3 rounded-lg text-left transition-all text-sm disabled:opacity-40"
                  style={selectedType === type.key ? {
                    border:"1px solid rgba(0,212,255,0.5)",
                    background:"rgba(0,212,255,0.08)",
                    boxShadow:"0 0 15px rgba(0,212,255,0.1)"
                  } : {
                    border:"1px solid rgba(255,255,255,0.06)",
                    background:"rgba(255,255,255,0.02)"
                  }}>
                  <span className="text-lg mb-1">{type.icon}</span>
                  <span className="font-semibold leading-tight" style={{ color: selectedType === type.key ? "#00d4ff" : "#cbd5e1" }}>{type.label}</span>
                  <span className="text-xs mt-0.5 leading-tight" style={{ color:"#4b5563" }}>{type.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div className="mt-4 rounded-lg px-4 py-3 text-sm flex items-center gap-2"
              style={{ background:"rgba(255,51,102,0.1)", border:"1px solid rgba(255,51,102,0.25)", color:"#ff3366" }}>
              <span>⚠</span> {error}
            </div>
          )}
        </div>

        {/* Main Tabs */}
        <div className="flex gap-0.5 overflow-x-auto" style={{ borderBottom:"1px solid rgba(255,255,255,0.06)" }}>
          {[
            { key: "audit",      label: "⏳ Progress",      disabled: !auditStatus },
            { key: "results",    label: "📊 Results",       disabled: !auditResults },
            { key: "competitor", label: "⚔️ Competitor",    disabled: false },
            { key: "gsc",        label: "🔎 Search Console", disabled: false },
            { key: "history",    label: `🕐 History (${auditHistory.length})`, disabled: false },
            { key: "benchmarks", label: "📊 Benchmarks", disabled: false },
            { key: "tools",      label: "🛠️ Tools",      disabled: false },
          ].map((tab) => (
            <button key={tab.key} onClick={() => !tab.disabled && setActiveTab(tab.key)} disabled={tab.disabled}
              className="px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors -mb-px"
              style={activeTab === tab.key
                ? { borderColor:"#00d4ff", color:"#00d4ff" }
                : { borderColor:"transparent", color: tab.disabled ? "#1f2937" : "#6b7280" }}>
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === "audit" && auditStatus && (
          <AuditProgress status={auditStatus} onViewResults={() => setActiveTab("results")} onDownload={handleDownloadZip} isCompleted={isCompleted} />
        )}
        {activeTab === "results" && auditResults && (
          <ReportViewer results={auditResults} reportFiles={reportFiles} onDownload={handleDownloadZip} token={token} auditId={currentAudit?.audit_id} apiBase={API} />
        )}
        {activeTab === "competitor" && <CompetitorPanel token={token} />}
        {activeTab === "gsc" && <SearchConsolePanel token={token} />}
        {activeTab === "tools" && <ToolsPanel token={token} />}
        {activeTab === "benchmarks" && (
          <BenchmarkPanel
            benchmarks={benchmarks}
            loading={benchmarkLoading}
            onLoad={loadBenchmarks}
            filterUrl={benchmarkUrl}
            setFilterUrl={setBenchmarkUrl}
          />
        )}

        {activeTab === "history" && (
          <div className="card">
            <h3 className="text-lg font-bold mb-4" style={{ color:"#e2e8f0" }}>
              <span className="neon-cyan">▸</span> Recent Audits
            </h3>
            {auditHistory.length === 0 ? (
              <p className="text-sm" style={{ color:"#4b5563" }}>No audits yet. Run your first audit above.</p>
            ) : (
              <div className="space-y-2">
                {auditHistory.map((audit) => (
                  <div key={audit.audit_id}
                    className="flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all"
                    style={{ border:"1px solid rgba(255,255,255,0.06)", background:"rgba(255,255,255,0.02)" }}
                    onMouseEnter={e => e.currentTarget.style.background="rgba(0,212,255,0.04)"}
                    onMouseLeave={e => e.currentTarget.style.background="rgba(255,255,255,0.02)"}
                    onClick={() => handleLoadHistoryAudit(audit)}>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate" style={{ color:"#cbd5e1" }}>{audit.url}</p>
                      <p className="text-xs mt-0.5 font-mono" style={{ color:"#374151" }}>
                        {audit.audit_type} · {new Date(audit.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="ml-4 flex items-center gap-2">
                      <span className={
                        audit.status === "completed" ? "badge-green" :
                        audit.status === "running"   ? "badge-blue"  :
                        audit.status === "failed"    ? "badge-red"   : "badge-yellow"
                      }>{audit.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Benchmark Panel ───────────────────────────────────────────────────────────

const SCORE_META = {
  performance:    { label: "Performance",    color: "#f97316", icon: "⚡" },
  seo:            { label: "SEO",            color: "#22c55e", icon: "🔎" },
  accessibility:  { label: "Accessibility",  color: "#00d4ff", icon: "♿" },
  best_practices: { label: "Best Practices", color: "#a78bfa", icon: "✅" },
  onpage:         { label: "On-Page SEO",    color: "#fbbf24", icon: "📄" },
};

function ScoreRing({ value, color, size = 68 }) {
  if (value == null) return <span className="text-xs" style={{ color:"#374151" }}>N/A</span>;
  const r = (size - 8) / 2;
  const circ = 2 * Math.PI * r;
  const dash = (value / 100) * circ;
  return (
    <svg width={size} height={size}>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth={6}/>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={6}
        strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
        style={{ transform:"rotate(-90deg)", transformOrigin:"50% 50%" }}/>
      <text x="50%" y="50%" dominantBaseline="middle" textAnchor="middle"
        style={{ fill: color, fontSize: size * 0.24, fontWeight: 700 }}>
        {value}
      </text>
    </svg>
  );
}

function BenchmarkPanel({ benchmarks, loading, onLoad, filterUrl, setFilterUrl }) {
  const [loaded, setLoaded] = useState(false);

  const handleLoad = (url) => { setLoaded(true); onLoad(url); };

  const audits  = benchmarks?.audits || [];
  const urls    = benchmarks?.available_urls || [];
  const latest  = audits[0];
  const prev    = audits[1];
  const keys    = Object.keys(SCORE_META);

  if (!loaded && !benchmarks) {
    return (
      <div className="card text-center py-12 space-y-4">
        <p className="text-4xl">📊</p>
        <div>
          <p className="text-lg font-bold" style={{ color:"#e2e8f0" }}>Audit Score Benchmarking</p>
          <p className="text-sm mt-2" style={{ color:"#4b5563" }}>
            Track PageSpeed &amp; on-page SEO scores over time.<br/>
            Compare each audit against the previous one.
          </p>
        </div>
        <button onClick={() => handleLoad("")} className="btn-primary mx-auto flex items-center gap-2">
          📊 Load Benchmarks
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="card flex flex-col items-center justify-center py-12 gap-4">
        <div className="animate-spin w-8 h-8 rounded-full"
          style={{ border:"2px solid rgba(0,212,255,0.2)", borderTopColor:"#00d4ff" }}/>
        <p className="text-sm" style={{ color:"#4b5563" }}>Loading score history...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <div className="card flex flex-wrap items-center gap-3">
        <p className="text-sm font-semibold" style={{ color:"#e2e8f0" }}>📊 Score History</p>
        {urls.length > 1 && (
          <select value={filterUrl}
            onChange={e => { setFilterUrl(e.target.value); handleLoad(e.target.value); }}
            className="input-field text-xs py-1.5 px-3" style={{ maxWidth:"300px" }}>
            <option value="">All URLs</option>
            {urls.map(u => <option key={u} value={u}>{u}</option>)}
          </select>
        )}
        <button onClick={() => handleLoad(filterUrl)}
          className="text-xs px-3 py-1.5 rounded-lg font-medium ml-auto"
          style={{ background:"rgba(255,255,255,0.05)", color:"#94a3b8", border:"1px solid rgba(255,255,255,0.08)" }}>
          ↻ Refresh
        </button>
      </div>

      {audits.length === 0 ? (
        <div className="card text-center py-8">
          <p className="text-sm" style={{ color:"#4b5563" }}>No completed audits found. Run an audit first.</p>
        </div>
      ) : (
        <>
          {/* Latest vs Previous comparison cards */}
          {latest && (
            <div className="card space-y-3">
              <p className="text-xs font-semibold uppercase tracking-widest" style={{ color:"#4b5563" }}>
                Latest vs Previous Audit
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                {keys.map(key => {
                  const meta  = SCORE_META[key];
                  const cur   = latest.scores?.[key];
                  const pval  = prev?.scores?.[key];
                  const delta = cur != null && pval != null ? cur - pval : null;
                  return (
                    <div key={key} className="flex flex-col items-center gap-2 p-3 rounded-xl"
                      style={{ background:"rgba(255,255,255,0.02)", border:"1px solid rgba(255,255,255,0.07)" }}>
                      <p className="text-xs font-semibold" style={{ color:"#6b7280" }}>{meta.icon} {meta.label}</p>
                      <ScoreRing value={cur} color={meta.color} />
                      <div className="text-xs flex items-center gap-1" style={{ color:"#4b5563" }}>
                        prev: <span style={{ color:"#94a3b8" }}>{pval ?? "—"}</span>
                        {delta != null && delta !== 0 && (
                          <span className="font-bold" style={{ color: delta > 0 ? "#22c55e" : "#ef4444" }}>
                            {delta > 0 ? "+" : ""}{delta}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
              <p className="text-xs" style={{ color:"#374151" }}>
                Latest: <span style={{ color:"#94a3b8" }}>{latest.url}</span> ·{" "}
                {new Date(latest.created_at).toLocaleDateString("en-IN", { day:"numeric", month:"short", year:"numeric" })}
              </p>
            </div>
          )}

          {/* Score history table */}
          <div className="card overflow-x-auto">
            <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color:"#4b5563" }}>
              Score History (last 10 audits)
            </p>
            <table className="w-full text-xs">
              <thead>
                <tr style={{ borderBottom:"1px solid rgba(255,255,255,0.06)" }}>
                  {["Date","URL","Type",...keys.map(k => SCORE_META[k].icon + " " + SCORE_META[k].label)].map(h => (
                    <th key={h} className="text-left py-2 px-3 font-semibold uppercase tracking-wide whitespace-nowrap"
                      style={{ color:"#4b5563" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {audits.map((a, i) => {
                  const prevRow = audits[i + 1];
                  return (
                    <tr key={a.audit_id} style={{ borderBottom:"1px solid rgba(255,255,255,0.03)" }}
                      className="transition-colors hover:bg-white hover:bg-opacity-5">
                      <td className="py-2.5 px-3 whitespace-nowrap" style={{ color:"#94a3b8" }}>
                        {new Date(a.created_at).toLocaleDateString("en-IN", { day:"numeric", month:"short" })}
                      </td>
                      <td className="py-2.5 px-3" style={{ maxWidth:"180px" }}>
                        <span className="truncate block font-mono" style={{ color:"#e2e8f0" }} title={a.url}>
                          {a.url.replace(/^https?:\/\//, "")}
                        </span>
                      </td>
                      <td className="py-2.5 px-3">
                        <span className="badge-blue">{a.audit_type}</span>
                      </td>
                      {keys.map(k => {
                        const cur  = a.scores?.[k];
                        const pval = prevRow?.scores?.[k];
                        return (
                          <td key={k} className="py-2.5 px-3 text-center">
                            {cur != null ? (
                              <span className="font-bold"
                                style={{ color: cur >= 90 ? "#22c55e" : cur >= 70 ? "#fbbf24" : "#ef4444" }}>
                                {cur}
                                {pval != null && cur !== pval && (
                                  <span className="text-xs font-normal ml-0.5"
                                    style={{ color: cur > pval ? "#22c55e" : "#ef4444" }}>
                                    {cur > pval ? "↑" : "↓"}
                                  </span>
                                )}
                              </span>
                            ) : <span style={{ color:"#374151" }}>—</span>}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
