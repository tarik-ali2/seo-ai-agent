import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── helpers ───────────────────────────────────────────────────────────────────

function PriBadge({ p }) {
  const cfg = {
    critical: { bg: "rgba(239,68,68,0.12)",  color: "#ef4444", border: "rgba(239,68,68,0.3)",  label: "🔴 Critical" },
    high:     { bg: "rgba(249,115,22,0.12)", color: "#f97316", border: "rgba(249,115,22,0.3)", label: "🟠 High" },
    medium:   { bg: "rgba(251,191,36,0.12)", color: "#fbbf24", border: "rgba(251,191,36,0.3)", label: "🟡 Medium" },
    low:      { bg: "rgba(34,197,94,0.12)",  color: "#22c55e", border: "rgba(34,197,94,0.3)",  label: "🟢 Low" },
  };
  const c = cfg[p] || cfg.low;
  return (
    <span className="text-xs font-semibold px-2 py-0.5 rounded-full whitespace-nowrap"
      style={{ color: c.color, background: c.bg, border: `1px solid ${c.border}` }}>
      {c.label}
    </span>
  );
}

function DualBar({ label, ourVal, compVal, ourDomain, compDomain }) {
  const our  = Math.max(2, ourVal  || 0);
  const comp = Math.max(2, compVal || 0);
  const ourWin = our >= comp;
  return (
    <div className="space-y-1.5 mb-4">
      <div className="flex justify-between text-xs font-medium" style={{ color:"#6b7280" }}>
        <span>{label}</span>
        <span style={{ color: ourWin ? "#22c55e" : "#ef4444" }}>{ourVal}/100 vs {compVal}/100</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs w-20 text-right truncate font-mono" style={{ color:"#00d4ff" }}>{ourDomain}</span>
        <div className="flex-1 rounded-full h-2.5 overflow-hidden" style={{ background:"rgba(255,255,255,0.05)" }}>
          <div className="h-2.5 rounded-full transition-all" style={{ width:`${our}%`, background:"#00d4ff" }}/>
        </div>
        <span className="text-xs" style={{ color:"#374151" }}>vs</span>
        <div className="flex-1 rounded-full h-2.5 overflow-hidden" style={{ background:"rgba(255,255,255,0.05)" }}>
          <div className="h-2.5 rounded-full transition-all float-right" style={{ width:`${comp}%`, background:"#ef4444" }}/>
        </div>
        <span className="text-xs w-20 truncate font-mono" style={{ color:"#ef4444" }}>{compDomain}</span>
      </div>
    </div>
  );
}

// ── main component ────────────────────────────────────────────────────────────

export default function CompetitorPanel({ token }) {
  const [ourUrl,  setOurUrl]  = useState("https://bechdu.in");
  const [compUrl, setCompUrl] = useState("https://www.cashify.in");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressMsg, setProgressMsg] = useState("");
  const [result,  setResult]  = useState(null);
  const [error,   setError]   = useState("");
  const [tab, setTab] = useState("overview");

  const runComparison = async () => {
    if (!ourUrl.trim() || !compUrl.trim()) { setError("Please enter both URLs"); return; }
    setLoading(true); setError(""); setResult(null); setProgress(5);
    setProgressMsg("Starting comparison...");

    try {
      const res = await fetch(`${API}/api/competitor/start`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ our_url: ourUrl.trim(), competitor_url: compUrl.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to start");

      const auditId = data.audit_id;
      const msgs = ["Crawling your site...", "Crawling competitor...", "Analyzing keyword gap...",
        "AI generating insights...", "Building Word document..."];
      let statusData = null;
      for (let i = 0; i < 120; i++) {
        await new Promise(r => setTimeout(r, 3000));
        const sr = await fetch(`${API}/api/audit/${auditId}/status`, { headers: { Authorization: `Bearer ${token}` } });
        statusData = await sr.json();
        setProgress(statusData.progress || Math.min(90, 10 + i * 2));
        setProgressMsg(statusData.progress_message || msgs[Math.floor(i / 5) % 5]);
        if (statusData.status === "completed" || statusData.status === "failed") break;
      }
      if (!statusData || statusData.status === "failed") throw new Error(statusData?.progress_message || "Comparison failed");
      if (statusData.status !== "completed") throw new Error("Comparison timed out");

      const rr = await fetch(`${API}/api/audit/${auditId}/results`, { headers: { Authorization: `Bearer ${token}` } });
      const rd = await rr.json();
      if (!rd.suggestions) throw new Error("Results not available");
      setResult({ ...rd.suggestions, audit_id: auditId });
      setProgress(100); setProgressMsg("Done!");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadDoc = () => {
    if (!result?.audit_id) return;
    fetch(`${API}/api/competitor/${result.audit_id}/download`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.blob()).then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url; a.download = "Competitor_SEO_Comparison.docx"; a.click();
        URL.revokeObjectURL(url);
      }).catch(() => setError("Download failed"));
  };

  const ourDomain  = result?.our_domain  || ourUrl.replace(/https?:\/\//,"").split("/")[0];
  const compDomain = result?.competitor_domain || compUrl.replace(/https?:\/\//,"").split("/")[0];
  const ai = result?.ai_insights || {};

  const tabs = [
    { key: "overview",     label: "Overview" },
    { key: "opportunities",label: `Opportunities (${result?.opportunities?.length || 0})` },
    { key: "keywords",     label: `Keyword Gap (${result?.keyword_gap?.length || 0})` },
    { key: "pages",        label: "Page Comparison" },
    { key: "battle_plan",  label: "🤖 AI Battle Plan" },
  ];

  return (
    <div className="card space-y-5">
      {/* Header */}
      <div className="flex items-center gap-3">
        <span className="text-2xl">⚔️</span>
        <div>
          <h2 className="text-xl font-bold" style={{ color:"#e2e8f0" }}>Competitor SEO Analysis</h2>
          <p className="text-sm" style={{ color:"#4b5563" }}>Side-by-side crawl · keyword gap · AI battle plan</p>
        </div>
      </div>

      {/* URL inputs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-semibold mb-1" style={{ color:"#00d4ff" }}>OUR WEBSITE</label>
          <input className="input-field" style={{ borderColor:"rgba(0,212,255,0.3)" }}
            value={ourUrl} onChange={e => setOurUrl(e.target.value)}
            placeholder="https://bechdu.in" disabled={loading} />
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1" style={{ color:"#ef4444" }}>COMPETITOR WEBSITE</label>
          <input className="input-field" style={{ borderColor:"rgba(239,68,68,0.3)" }}
            value={compUrl} onChange={e => setCompUrl(e.target.value)}
            placeholder="https://cashify.in" disabled={loading} />
        </div>
      </div>

      <button onClick={runComparison} disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
        {loading ? (
          <>
            <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
            </svg>
            {progressMsg || "Running..."}
          </>
        ) : "⚔️ Run Competitor Comparison"}
      </button>

      {/* Progress bar */}
      {loading && (
        <div>
          <div className="flex justify-between text-xs mb-1" style={{ color:"#4b5563" }}>
            <span>{progressMsg}</span><span style={{ color:"#00d4ff" }}>{progress}%</span>
          </div>
          <div className="w-full rounded-full h-2 overflow-hidden" style={{ background:"rgba(255,255,255,0.05)" }}>
            <div className="h-2 rounded-full transition-all" style={{ width:`${progress}%`, background:"linear-gradient(90deg,#0066aa,#00d4ff)" }}/>
          </div>
        </div>
      )}

      {error && (
        <div className="rounded-lg px-4 py-3 text-sm flex items-center gap-2"
          style={{ background:"rgba(239,68,68,0.08)", border:"1px solid rgba(239,68,68,0.25)", color:"#ef4444" }}>
          ⚠ {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <>
          {/* Verdict banner */}
          {result.verdict && (
            <div className="rounded-xl p-4 flex items-center justify-between flex-wrap gap-3"
              style={{ background:"rgba(0,212,255,0.06)", border:"1px solid rgba(0,212,255,0.2)" }}>
              <div>
                <p className="font-bold text-lg" style={{ color:"#e2e8f0" }}>
                  Verdict: <span style={{ color: result.verdict.color === "critical" ? "#ef4444" : result.verdict.color === "high" ? "#f97316" : "#22c55e" }}>
                    {result.verdict.status}
                  </span>
                </p>
                <p className="text-sm mt-0.5" style={{ color:"#6b7280" }}>{result.verdict.summary}</p>
              </div>
              <button onClick={downloadDoc} className="btn-primary flex items-center gap-2 text-sm whitespace-nowrap">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                </svg>
                Download .docx
              </button>
            </div>
          )}

          {/* Section tabs */}
          <div className="flex gap-0.5 overflow-x-auto" style={{ borderBottom:"1px solid rgba(255,255,255,0.06)" }}>
            {tabs.map(t => (
              <button key={t.key} onClick={() => setTab(t.key)}
                className="px-3 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors -mb-px"
                style={tab === t.key
                  ? { borderColor:"#00d4ff", color:"#00d4ff" }
                  : { borderColor:"transparent", color:"#6b7280" }}>
                {t.label}
              </button>
            ))}
          </div>

          {/* ── Overview ────────────────────────────────────────────────── */}
          {tab === "overview" && (
            <div className="space-y-4">
              {/* 4 stat cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { label: "Our Score",   val: result.our_stats?.onpage_avg_score,         color: "#00d4ff" },
                  { label: "Their Score", val: result.competitor_stats?.onpage_avg_score,   color: "#ef4444" },
                  { label: "Score Gap",   val: `${Math.abs(result.verdict?.gap || 0)} pts`, color: result.verdict?.gap > 0 ? "#ef4444" : "#22c55e" },
                  { label: "Keyword Gap", val: result.keyword_gap?.length || 0,             color: "#f97316" },
                ].map(c => (
                  <div key={c.label} className="text-center p-4 rounded-xl"
                    style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.07)" }}>
                    <p className="text-xs font-medium uppercase tracking-widest" style={{ color:"#4b5563" }}>{c.label}</p>
                    <p className="text-2xl font-black mt-1" style={{ color: c.color }}>{c.val}</p>
                  </div>
                ))}
              </div>

              <DualBar label="On-Page SEO Score"
                ourVal={result.our_stats?.onpage_avg_score}
                compVal={result.competitor_stats?.onpage_avg_score}
                ourDomain={ourDomain} compDomain={compDomain} />
              <DualBar label="Technical SEO Score"
                ourVal={result.our_stats?.score}
                compVal={result.competitor_stats?.score}
                ourDomain={ourDomain} compDomain={compDomain} />

              {/* Quick stats table */}
              <div className="overflow-x-auto rounded-xl" style={{ border:"1px solid rgba(255,255,255,0.07)" }}>
                <table className="w-full text-sm">
                  <thead>
                    <tr style={{ background:"rgba(255,255,255,0.04)" }}>
                      <th className="text-left p-3 font-semibold" style={{ color:"#6b7280" }}>Factor</th>
                      <th className="p-3 text-center font-semibold" style={{ color:"#00d4ff" }}>{ourDomain}</th>
                      <th className="p-3 text-center font-semibold" style={{ color:"#ef4444" }}>{compDomain}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      ["HTTPS",          result.our_stats?.https       ? "✅" : "❌", result.competitor_stats?.https       ? "✅" : "❌"],
                      ["robots.txt",     result.our_stats?.robots_txt  ? "✅" : "❌", result.competitor_stats?.robots_txt  ? "✅" : "❌"],
                      ["Sitemap URLs",   result.our_stats?.sitemap_urls  || 0,        result.competitor_stats?.sitemap_urls  || 0],
                      ["Pages w/ Title", result.our_stats?.pages_with_title || 0,     result.competitor_stats?.pages_with_title || 0],
                      ["Pages w/ Meta",  result.our_stats?.pages_with_meta  || 0,     result.competitor_stats?.pages_with_meta  || 0],
                      ["Pages w/ Schema",result.our_stats?.pages_with_schema || 0,    result.competitor_stats?.pages_with_schema || 0],
                      ["Avg Word Count", result.our_stats?.avg_word_count || 0,       result.competitor_stats?.avg_word_count || 0],
                    ].map(([label, our, comp]) => (
                      <tr key={label} style={{ borderTop:"1px solid rgba(255,255,255,0.04)" }}>
                        <td className="p-3 font-medium" style={{ color:"#94a3b8" }}>{label}</td>
                        <td className="p-3 text-center font-bold" style={{ color:"#00d4ff" }}>{our}</td>
                        <td className="p-3 text-center font-bold" style={{ color:"#ef4444" }}>{comp}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ── Opportunities ────────────────────────────────────────────── */}
          {tab === "opportunities" && (
            <div className="space-y-3">
              {(result.opportunities || []).length === 0 ? (
                <p className="text-sm text-center py-6" style={{ color:"#4b5563" }}>No opportunities found.</p>
              ) : (result.opportunities || []).map((opp, i) => (
                <div key={i} className="rounded-xl p-4"
                  style={{
                    background: opp.priority === "critical" ? "rgba(239,68,68,0.06)" : opp.priority === "high" ? "rgba(249,115,22,0.06)" : "rgba(255,255,255,0.03)",
                    border: `1px solid ${opp.priority === "critical" ? "rgba(239,68,68,0.2)" : opp.priority === "high" ? "rgba(249,115,22,0.2)" : "rgba(255,255,255,0.08)"}`,
                    borderLeft: `4px solid ${opp.priority === "critical" ? "#ef4444" : opp.priority === "high" ? "#f97316" : opp.priority === "medium" ? "#fbbf24" : "#22c55e"}`,
                  }}>
                  <div className="flex items-start gap-3">
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <PriBadge p={opp.priority} />
                        <span className="font-semibold text-sm" style={{ color:"#e2e8f0" }}>{opp.area}</span>
                      </div>
                      <p className="text-xs" style={{ color:"#6b7280" }}>{opp.gap}</p>
                      <div className="rounded-lg px-3 py-2"
                        style={{ background:"rgba(34,197,94,0.06)", border:"1px solid rgba(34,197,94,0.15)" }}>
                        <span className="text-xs font-semibold" style={{ color:"#22c55e" }}>Action: </span>
                        <span className="text-xs" style={{ color:"#94a3b8" }}>{opp.action}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* ── Keyword Gap ──────────────────────────────────────────────── */}
          {tab === "keywords" && (
            <div className="space-y-4">
              {/* Missing keywords summary */}
              <div className="rounded-xl p-4 space-y-3"
                style={{ background:"rgba(239,68,68,0.05)", border:"1px solid rgba(239,68,68,0.15)" }}>
                <h4 className="font-semibold text-sm" style={{ color:"#ef4444" }}>
                  ❌ Keywords {compDomain} ranks for — {ourDomain} is missing ({result.keyword_gap?.length || 0})
                </h4>
                <div className="flex flex-wrap gap-2">
                  {(result.keyword_gap || []).slice(0, 30).map((kw, i) => (
                    <span key={i} className="px-2.5 py-1 text-xs rounded-full font-medium"
                      style={{ background:"rgba(239,68,68,0.1)", border:"1px solid rgba(239,68,68,0.2)", color:"#f87171" }}>
                      {kw}
                    </span>
                  ))}
                </div>
              </div>

              {/* Our unique keywords */}
              {(result.our_unique_keywords || []).length > 0 && (
                <div className="rounded-xl p-4 space-y-3"
                  style={{ background:"rgba(34,197,94,0.05)", border:"1px solid rgba(34,197,94,0.15)" }}>
                  <h4 className="font-semibold text-sm" style={{ color:"#22c55e" }}>
                    ✅ Keywords only {ourDomain} has ({result.our_unique_keywords.length})
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {result.our_unique_keywords.slice(0, 20).map((kw, i) => (
                      <span key={i} className="px-2.5 py-1 text-xs rounded-full font-medium"
                        style={{ background:"rgba(34,197,94,0.1)", border:"1px solid rgba(34,197,94,0.2)", color:"#4ade80" }}>
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Content ideas table */}
              {(result.content_ideas || []).length > 0 && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color:"#4b5563" }}>
                    💡 Content Strategy to Close the Gap
                  </p>
                  <div className="overflow-x-auto rounded-xl" style={{ border:"1px solid rgba(255,255,255,0.07)" }}>
                    <table className="w-full text-xs">
                      <thead>
                        <tr style={{ background:"rgba(255,255,255,0.04)" }}>
                          {["Priority", "Target Keyword", "Content Type", "Suggested Title"].map(h => (
                            <th key={h} className="text-left p-3 font-semibold uppercase tracking-wide" style={{ color:"#4b5563" }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {result.content_ideas.map((idea, i) => (
                          <tr key={i} style={{ borderTop:"1px solid rgba(255,255,255,0.04)" }}>
                            <td className="p-3"><PriBadge p={idea.priority} /></td>
                            <td className="p-3 font-mono font-semibold" style={{ color:"#00d4ff" }}>{idea.keyword}</td>
                            <td className="p-3">
                              <span className="badge-blue">{idea.content_type}</span>
                            </td>
                            <td className="p-3" style={{ color:"#94a3b8" }}>{idea.suggested_title}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── Page Comparison ──────────────────────────────────────────── */}
          {tab === "pages" && (
            <div className="space-y-3">
              {(result.page_comparison || []).map((pc, i) => (
                <div key={i} className="rounded-xl overflow-hidden"
                  style={{ border:"1px solid rgba(255,255,255,0.07)" }}>
                  <div className="px-4 py-2 flex items-center justify-between"
                    style={{ background:"rgba(255,255,255,0.04)" }}>
                    <span className="text-sm font-medium" style={{ color:"#94a3b8" }}>Page {i + 1}</span>
                    <span className="text-xs font-bold px-2 py-0.5 rounded-full"
                      style={pc.winner === ourDomain
                        ? { background:"rgba(0,212,255,0.12)", color:"#00d4ff", border:"1px solid rgba(0,212,255,0.3)" }
                        : pc.winner === compDomain
                        ? { background:"rgba(239,68,68,0.12)", color:"#ef4444", border:"1px solid rgba(239,68,68,0.3)" }
                        : { background:"rgba(255,255,255,0.05)", color:"#6b7280", border:"1px solid rgba(255,255,255,0.1)" }}>
                      Winner: {pc.winner}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 divide-x" style={{ "--tw-divide-opacity":1, borderColor:"rgba(255,255,255,0.06)" }}>
                    {[
                      { domain: ourDomain,  url: pc.our_url,  title: pc.our_title,  h1: pc.our_h1,  words: pc.our_word_count,  score: pc.our_score,  isOur: true },
                      { domain: compDomain, url: pc.comp_url, title: pc.comp_title, h1: pc.comp_h1, words: pc.comp_word_count, score: pc.comp_score, isOur: false },
                    ].map((side, j) => (
                      <div key={j} className="p-3 space-y-2" style={{ borderLeft: j > 0 ? "1px solid rgba(255,255,255,0.06)" : "none" }}>
                        <div className="text-xs font-bold flex items-center gap-2"
                          style={{ color: side.isOur ? "#00d4ff" : "#ef4444" }}>
                          {side.domain}
                          <span className="font-normal px-1.5 py-0.5 rounded text-xs"
                            style={{
                              background: (side.score || 0) >= 70 ? "rgba(34,197,94,0.1)" : (side.score || 0) >= 40 ? "rgba(251,191,36,0.1)" : "rgba(239,68,68,0.1)",
                              color:      (side.score || 0) >= 70 ? "#22c55e"              : (side.score || 0) >= 40 ? "#fbbf24"              : "#ef4444",
                            }}>
                            {side.score || 0}/100
                          </span>
                        </div>
                        <div className="text-xs truncate font-mono" style={{ color:"#374151" }}>{side.url}</div>
                        <div className="text-xs"><span style={{ color:"#4b5563" }}>Title: </span>
                          <span style={{ color: side.title ? "#94a3b8" : "#ef4444" }}>{side.title || "❌ Missing"}</span>
                        </div>
                        <div className="text-xs"><span style={{ color:"#4b5563" }}>H1: </span>
                          <span style={{ color: side.h1 ? "#94a3b8" : "#ef4444" }}>{side.h1 || "❌ Missing"}</span>
                        </div>
                        <div className="text-xs" style={{ color:"#4b5563" }}>{side.words || 0} words</div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* ── AI Battle Plan ───────────────────────────────────────────── */}
          {tab === "battle_plan" && (
            <div className="space-y-4">
              {ai.error ? (
                <div className="card text-center py-8">
                  <p className="text-sm" style={{ color:"#ef4444" }}>AI insights unavailable: {ai.error}</p>
                </div>
              ) : !ai.strategic_summary ? (
                <div className="card text-center py-8">
                  <p className="text-sm" style={{ color:"#4b5563" }}>No AI battle plan in results — re-run the comparison to generate one.</p>
                </div>
              ) : (
                <>
                  {/* Strategic summary */}
                  <div className="rounded-xl p-5 space-y-2"
                    style={{ background:"rgba(0,212,255,0.05)", border:"1px solid rgba(0,212,255,0.15)" }}>
                    <p className="text-xs font-semibold uppercase tracking-widest" style={{ color:"#00d4ff" }}>🧠 Strategic Summary</p>
                    <p className="text-sm leading-relaxed" style={{ color:"#94a3b8" }}>{ai.strategic_summary}</p>
                  </div>

                  {/* Biggest opportunity */}
                  <div className="rounded-xl p-5 space-y-2"
                    style={{ background:"rgba(34,197,94,0.05)", border:"1px solid rgba(34,197,94,0.2)" }}>
                    <p className="text-xs font-semibold uppercase tracking-widest" style={{ color:"#22c55e" }}>🎯 Biggest Single Opportunity</p>
                    <p className="text-sm leading-relaxed font-medium" style={{ color:"#e2e8f0" }}>{ai.biggest_opportunity}</p>
                  </div>

                  {/* Content strategy */}
                  {ai.content_strategy?.length > 0 && (
                    <div className="card space-y-3">
                      <p className="text-xs font-semibold uppercase tracking-widest" style={{ color:"#4b5563" }}>📝 Content Strategy (3 Pieces to Rank)</p>
                      {ai.content_strategy.map((item, i) => (
                        <div key={i} className="flex gap-3 p-3 rounded-lg"
                          style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.07)" }}>
                          <span className="text-xs font-black w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0"
                            style={{ background:"rgba(0,212,255,0.15)", color:"#00d4ff" }}>{i + 1}</span>
                          <p className="text-sm" style={{ color:"#94a3b8" }}>{item}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Quick wins + Timeline in 2 columns */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {ai.quick_wins?.length > 0 && (
                      <div className="card space-y-3">
                        <p className="text-xs font-semibold uppercase tracking-widest" style={{ color:"#4b5563" }}>⚡ Quick Wins (under 1 week)</p>
                        {ai.quick_wins.map((w, i) => (
                          <div key={i} className="flex items-start gap-2 text-sm">
                            <span style={{ color:"#22c55e" }}>☑</span>
                            <span style={{ color:"#94a3b8" }}>{w}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    {ai.realistic_timeline && (
                      <div className="card space-y-2">
                        <p className="text-xs font-semibold uppercase tracking-widest" style={{ color:"#4b5563" }}>📅 Realistic Timeline</p>
                        <p className="text-sm leading-relaxed" style={{ color:"#94a3b8" }}>{ai.realistic_timeline}</p>
                      </div>
                    )}
                  </div>

                  {/* Risk if ignored */}
                  {ai.risk_if_ignored && (
                    <div className="rounded-xl p-4 space-y-2"
                      style={{ background:"rgba(239,68,68,0.06)", border:"1px solid rgba(239,68,68,0.2)" }}>
                      <p className="text-xs font-semibold uppercase tracking-widest" style={{ color:"#ef4444" }}>⚠ Risk If Ignored (3 months)</p>
                      <p className="text-sm leading-relaxed" style={{ color:"#94a3b8" }}>{ai.risk_if_ignored}</p>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
