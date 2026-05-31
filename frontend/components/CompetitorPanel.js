import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function ScoreBar({ label, ourScore, compScore, ourDomain, compDomain }) {
  const ourW  = Math.max(4, ourScore);
  const compW = Math.max(4, compScore);
  const ourWin  = ourScore >= compScore;
  const compWin = compScore > ourScore;
  return (
    <div className="mb-4">
      <div className="flex justify-between text-xs font-medium text-gray-600 mb-1">
        <span>{label}</span>
        <span className={ourWin ? "text-green-600 font-bold" : "text-red-500"}>{ourScore}/100</span>
      </div>
      <div className="flex gap-2 items-center">
        <span className="text-xs text-blue-600 w-20 text-right truncate">{ourDomain}</span>
        <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden flex">
          <div className="h-3 rounded-l-full bg-blue-500 transition-all" style={{ width: `${ourW}%` }}/>
        </div>
        <span className="text-xs text-gray-400">vs</span>
        <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden flex justify-end">
          <div className="h-3 rounded-r-full bg-red-400 transition-all" style={{ width: `${compW}%` }}/>
        </div>
        <span className="text-xs text-red-500 w-20 truncate">{compDomain}</span>
        <span className={`text-xs w-16 text-right font-bold ${compWin ? "text-red-500" : "text-green-600"}`}>{compScore}/100</span>
      </div>
    </div>
  );
}

function PriorityBadge({ priority }) {
  const map = {
    critical: "bg-red-100 text-red-700 border border-red-200",
    high:     "bg-orange-100 text-orange-700 border border-orange-200",
    medium:   "bg-yellow-100 text-yellow-700 border border-yellow-200",
    low:      "bg-green-100 text-green-700 border border-green-200",
  };
  const labels = { critical: "🔴 Critical", high: "🟠 High", medium: "🟡 Medium", low: "🟢 Low" };
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${map[priority] || map.low}`}>
      {labels[priority] || priority}
    </span>
  );
}

export default function CompetitorPanel({ token }) {
  const [ourUrl,  setOurUrl]  = useState("https://bechdu.in");
  const [compUrl, setCompUrl] = useState("https://www.cashify.in");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressMsg, setProgressMsg] = useState("");
  const [result, setResult]   = useState(null);
  const [error,  setError]    = useState("");
  const [activeSection, setActiveSection] = useState("overview");
  const pollRef = useState(null);

  const runComparison = async () => {
    if (!ourUrl.trim() || !compUrl.trim()) {
      setError("Please enter both URLs"); return;
    }
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
      if (!auditId) throw new Error("No audit ID returned from server");

      // Poll status for this specific audit
      const msgs = ["Crawling your site...", "Crawling competitor site...", "Analyzing keyword gap...",
        "Generating comparison...", "Building Word document..."];
      let statusData = null;
      for (let i = 0; i < 120; i++) {
        await new Promise(r => setTimeout(r, 3000));

        const statusRes = await fetch(`${API}/api/audit/${auditId}/status`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        statusData = await statusRes.json();
        setProgress(statusData.progress || Math.min(90, 10 + i * 2));
        setProgressMsg(statusData.progress_message || msgs[Math.floor(i / 5) % 5]);

        if (statusData.status === "completed" || statusData.status === "failed") break;
      }

      if (!statusData || statusData.status === "failed")
        throw new Error(statusData?.progress_message || "Comparison failed");
      if (statusData.status !== "completed") throw new Error("Comparison timed out");

      // Fetch results
      const resData = await fetch(`${API}/api/audit/${auditId}/results`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const resultData = await resData.json();
      if (!resultData.suggestions) throw new Error("Results not available yet");
      setResult({ ...resultData.suggestions, audit_id: auditId });
      setProgress(100); setProgressMsg("Done!");

    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadDoc = () => {
    if (!result?.audit_id) return;
    fetch(`${API}/api/competitor/${result.audit_id}/download`, {
      headers: { Authorization: `Bearer ${token}` },
    }).then(r => r.blob()).then(blob => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = "Competitor_SEO_Comparison.docx"; a.click();
      URL.revokeObjectURL(url);
    }).catch(() => setError("Download failed"));
  };

  const ourDomain  = result?.our_domain  || ourUrl.replace(/https?:\/\//,"").split("/")[0];
  const compDomain = result?.competitor_domain || compUrl.replace(/https?:\/\//,"").split("/")[0];

  const sections = [
    { key: "overview",     label: "Overview" },
    { key: "opportunities",label: `Opportunities (${result?.opportunities?.length || 0})` },
    { key: "keywords",     label: "Keyword Gap" },
    { key: "pages",        label: "Page Comparison" },
    { key: "plan",         label: "Action Plan" },
  ];

  return (
    <div className="card space-y-5">
      <div className="flex items-center gap-3">
        <span className="text-2xl">⚔️</span>
        <div>
          <h2 className="text-xl font-bold text-gray-900">Competitor SEO Comparison</h2>
          <p className="text-sm text-gray-500">Side-by-side analysis + keyword gap + action plan</p>
        </div>
      </div>

      {/* URL inputs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-semibold text-blue-600 mb-1">OUR WEBSITE</label>
          <input className="input-field border-blue-300" value={ourUrl}
            onChange={e => setOurUrl(e.target.value)} placeholder="https://bechdu.in"
            disabled={loading} />
        </div>
        <div>
          <label className="block text-xs font-semibold text-red-500 mb-1">COMPETITOR WEBSITE</label>
          <input className="input-field border-red-300" value={compUrl}
            onChange={e => setCompUrl(e.target.value)} placeholder="https://cashify.in"
            disabled={loading} />
        </div>
      </div>

      <button onClick={runComparison} disabled={loading}
        className="btn-primary w-full flex items-center justify-center gap-2">
        {loading ? (
          <>
            <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
            </svg>
            {progressMsg || "Running comparison..."}
          </>
        ) : "⚔️ Run Competitor Comparison"}
      </button>

      {/* Progress bar */}
      {loading && (
        <div>
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>{progressMsg}</span><span>{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <div className="h-2 rounded-full progress-bar-animated" style={{ width: `${progress}%` }}/>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">⚠️ {error}</div>
      )}

      {/* Results */}
      {result && (
        <>
          {/* Verdict banner */}
          <div className={`rounded-xl p-4 border-2 ${
            result.verdict?.color === "critical" ? "bg-red-50 border-red-300" :
            result.verdict?.color === "high"     ? "bg-orange-50 border-orange-300" :
            result.verdict?.color === "medium"   ? "bg-yellow-50 border-yellow-300" :
            "bg-green-50 border-green-300"
          }`}>
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div>
                <p className="font-bold text-gray-900 text-lg">Verdict: {result.verdict?.status}</p>
                <p className="text-sm text-gray-600 mt-0.5">{result.verdict?.summary}</p>
              </div>
              <button onClick={downloadDoc}
                className="btn-primary flex items-center gap-2 text-sm whitespace-nowrap">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                </svg>
                Download Comparison.docx
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 border-b border-gray-200 overflow-x-auto">
            {sections.map(s => (
              <button key={s.key} onClick={() => setActiveSection(s.key)}
                className={`px-3 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors -mb-px ${
                  activeSection === s.key
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                }`}>
                {s.label}
              </button>
            ))}
          </div>

          {/* Overview */}
          {activeSection === "overview" && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { label: "Our Score",   val: result.our_stats?.onpage_avg_score,   color: "blue"  },
                  { label: "Their Score", val: result.competitor_stats?.onpage_avg_score, color: "red" },
                  { label: "Gap",         val: `${Math.abs(result.verdict?.gap || 0)} pts`, color: result.verdict?.gap > 0 ? "red" : "green" },
                  { label: "Keyword Gap", val: result.keyword_gap?.length || 0, color: "purple" },
                ].map(item => (
                  <div key={item.label} className="text-center p-4 bg-gray-50 rounded-xl border border-gray-200">
                    <p className="text-xs text-gray-500 font-medium">{item.label}</p>
                    <p className={`text-2xl font-bold mt-1 text-${item.color}-600`}>{item.val}</p>
                  </div>
                ))}
              </div>

              <ScoreBar label="On-Page SEO Score"
                ourScore={result.our_stats?.onpage_avg_score || 0}
                compScore={result.competitor_stats?.onpage_avg_score || 0}
                ourDomain={ourDomain} compDomain={compDomain} />
              <ScoreBar label="Technical SEO Score"
                ourScore={result.our_stats?.score || 0}
                compScore={result.competitor_stats?.score || 0}
                ourDomain={ourDomain} compDomain={compDomain} />

              {/* Quick stats table */}
              <div className="overflow-x-auto">
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr>
                      <th className="text-left p-2 bg-gray-800 text-white rounded-tl-lg">Factor</th>
                      <th className="p-2 bg-blue-600 text-white">{ourDomain}</th>
                      <th className="p-2 bg-red-500 text-white rounded-tr-lg">{compDomain}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      ["HTTPS", result.our_stats?.https ? "✅" : "❌", result.competitor_stats?.https ? "✅" : "❌"],
                      ["robots.txt", result.our_stats?.robots_txt ? "✅" : "❌", result.competitor_stats?.robots_txt ? "✅" : "❌"],
                      ["Sitemap URLs", result.our_stats?.sitemap_urls || 0, result.competitor_stats?.sitemap_urls || 0],
                      ["Pages w/ Title", result.our_stats?.pages_with_title || 0, result.competitor_stats?.pages_with_title || 0],
                      ["Pages w/ Meta", result.our_stats?.pages_with_meta || 0, result.competitor_stats?.pages_with_meta || 0],
                      ["Pages w/ Schema", result.our_stats?.pages_with_schema || 0, result.competitor_stats?.pages_with_schema || 0],
                      ["Avg Word Count", result.our_stats?.avg_word_count || 0, result.competitor_stats?.avg_word_count || 0],
                    ].map(([label, our, comp]) => (
                      <tr key={label} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="p-2 font-medium text-gray-700">{label}</td>
                        <td className="p-2 text-center font-semibold text-blue-700">{our}</td>
                        <td className="p-2 text-center font-semibold text-red-600">{comp}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Opportunities */}
          {activeSection === "opportunities" && (
            <div className="space-y-3">
              {(result.opportunities || []).map((opp, i) => (
                <div key={i} className={`rounded-xl border-l-4 p-4 ${
                  opp.priority === "critical" ? "border-red-500 bg-red-50" :
                  opp.priority === "high"     ? "border-orange-400 bg-orange-50" :
                  opp.priority === "medium"   ? "border-yellow-400 bg-yellow-50" :
                  "border-green-400 bg-green-50"
                }`}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <PriorityBadge priority={opp.priority} />
                        <span className="font-semibold text-gray-900 text-sm">{opp.area}</span>
                      </div>
                      <p className="text-xs text-gray-600 mb-2">{opp.gap}</p>
                      <div className="bg-white rounded-lg px-3 py-2 border border-green-200">
                        <span className="text-xs font-semibold text-green-700">Action: </span>
                        <span className="text-xs text-gray-700">{opp.action}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Keyword Gap */}
          {activeSection === "keywords" && (
            <div className="space-y-4">
              <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                <h4 className="font-semibold text-red-700 mb-2">
                  ❌ Keywords {compDomain} has — {ourDomain} is missing ({result.keyword_gap?.length || 0} keywords)
                </h4>
                <div className="flex flex-wrap gap-2">
                  {(result.keyword_gap || []).slice(0, 20).map((kw, i) => (
                    <span key={i} className="px-2.5 py-1 bg-white border border-red-200 text-red-700 text-xs rounded-full font-medium">
                      {kw}
                    </span>
                  ))}
                </div>
              </div>

              {(result.our_unique_keywords || []).length > 0 && (
                <div className="bg-green-50 border border-green-200 rounded-xl p-4">
                  <h4 className="font-semibold text-green-700 mb-2">
                    ✅ Keywords only {ourDomain} has ({result.our_unique_keywords.length})
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {result.our_unique_keywords.slice(0, 15).map((kw, i) => (
                      <span key={i} className="px-2.5 py-1 bg-white border border-green-200 text-green-700 text-xs rounded-full font-medium">
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {(result.content_ideas || []).length > 0 && (
                <div>
                  <h4 className="font-semibold text-gray-800 mb-3">💡 Content Ideas to Close the Gap</h4>
                  <div className="space-y-2">
                    {result.content_ideas.map((idea, i) => (
                      <div key={i} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                        <PriorityBadge priority={idea.priority} />
                        <div>
                          <p className="text-sm font-medium text-gray-900">{idea.keyword}</p>
                          <p className="text-xs text-gray-500">{idea.content_type} — {idea.suggested_title}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Page comparison */}
          {activeSection === "pages" && (
            <div className="space-y-4">
              {(result.page_comparison || []).map((pc, i) => (
                <div key={i} className="border border-gray-200 rounded-xl overflow-hidden">
                  <div className="bg-gray-50 px-4 py-2 flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Page {i+1}</span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                      pc.winner === ourDomain ? "bg-blue-100 text-blue-700" :
                      pc.winner === compDomain ? "bg-red-100 text-red-700" :
                      "bg-gray-100 text-gray-600"
                    }`}>
                      Winner: {pc.winner}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 divide-x divide-gray-200">
                    {[
                      { domain: ourDomain, url: pc.our_url, title: pc.our_title, meta: pc.our_meta, h1: pc.our_h1, words: pc.our_word_count, score: pc.our_score, isOur: true },
                      { domain: compDomain, url: pc.comp_url, title: pc.comp_title, meta: pc.comp_meta, h1: pc.comp_h1, words: pc.comp_word_count, score: pc.comp_score, isOur: false },
                    ].map((side, j) => (
                      <div key={j} className="p-3 space-y-2">
                        <div className={`text-xs font-bold ${side.isOur ? "text-blue-600" : "text-red-500"}`}>
                          {side.domain}
                          <span className={`ml-2 font-normal px-1.5 py-0.5 rounded ${
                            side.score >= 70 ? "bg-green-100 text-green-700" :
                            side.score >= 40 ? "bg-yellow-100 text-yellow-700" :
                            "bg-red-100 text-red-700"
                          }`}>{side.score}/100</span>
                        </div>
                        <div className="text-xs text-gray-400 truncate">{side.url}</div>
                        <div>
                          <span className="text-xs text-gray-400">Title: </span>
                          <span className={`text-xs ${!side.title ? "text-red-500 italic" : "text-gray-700"}`}>
                            {side.title || "❌ Missing"}
                          </span>
                        </div>
                        <div>
                          <span className="text-xs text-gray-400">H1: </span>
                          <span className={`text-xs ${!side.h1 ? "text-red-500 italic" : "text-gray-700"}`}>
                            {side.h1 || "❌ Missing"}
                          </span>
                        </div>
                        <div className="text-xs text-gray-500">{side.words} words</div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Action Plan */}
          {activeSection === "plan" && (
            <div className="space-y-4">
              {[
                { week: "Week 1", color: "red", title: "Critical Fixes", items: [
                  `Fix title tag — currently '${ourDomain}' on every page — add keyword + brand`,
                  "Add unique meta description (150-160 chars) to every page",
                  "Fix multiple H1 tags — keep only ONE H1 per page",
                  "Add canonical tag to every page",
                  "Submit sitemap to Google Search Console",
                ]},
                { week: "Week 2", color: "orange", title: "On-Page SEO", items: [
                  "Add Organization schema JSON-LD to homepage",
                  "Add Product schema to all sell/buy pages",
                  "Add og:title, og:description, og:image to all pages",
                  `Add top missing keyword '${(result.keyword_gap || ["sell old phone"])[0]}' to homepage title`,
                  "Add 3+ H2 subheadings to structure content",
                ]},
                { week: "Week 3", color: "yellow", title: "Content Creation", items: [
                  "Write 500+ word intro content for homepage",
                  "Create landing pages for keyword gap terms",
                  "Add FAQ section to homepage and sell pages",
                  "Add 200+ word descriptions to all product pages",
                ]},
                { week: "Week 4", color: "green", title: "Technical + Tracking", items: [
                  "Verify GTM, GA4, Meta Pixel on all pages",
                  "Run PageSpeed — convert images to WebP",
                  "Set up Google Search Console monitoring",
                  "Run weekly automated audit with this agent",
                ]},
              ].map(({ week, color, title, items }) => (
                <div key={week} className={`border-l-4 pl-4 border-${color}-400`}>
                  <h4 className={`font-bold text-${color}-700 mb-2`}>{week} — {title}</h4>
                  <ul className="space-y-1.5">
                    {items.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                        <span className="mt-0.5 text-gray-400">☐</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
