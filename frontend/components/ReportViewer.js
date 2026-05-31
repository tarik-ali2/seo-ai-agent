import { useState } from "react";

// ── Shared helpers ─────────────────────────────────────────────────────────────

const PRIORITY_STYLE = {
  critical: "border-l-4 border-red-500 bg-red-50",
  high:     "border-l-4 border-orange-400 bg-orange-50",
  medium:   "border-l-4 border-yellow-400 bg-yellow-50",
  low:      "border-l-4 border-green-400 bg-green-50",
};
const PRIORITY_BADGE = {
  critical: "bg-red-100 text-red-700 border border-red-200",
  high:     "bg-orange-100 text-orange-700 border border-orange-200",
  medium:   "bg-yellow-100 text-yellow-700 border border-yellow-200",
  low:      "bg-green-100 text-green-700 border border-green-200",
};
const PRIORITY_ICON = { critical: "🔴", high: "🟠", medium: "🟡", low: "🟢" };

function Badge({ priority, label }) {
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${PRIORITY_BADGE[priority] || PRIORITY_BADGE.medium}`}>
      {PRIORITY_ICON[priority]} {label || priority}
    </span>
  );
}

function ScoreCircle({ score, size = "md" }) {
  const color = score >= 80 ? "#22c55e" : score >= 50 ? "#f59e0b" : "#ef4444";
  const sz = size === "sm" ? "w-14 h-14" : "w-20 h-20";
  const textSz = size === "sm" ? "text-lg" : "text-2xl";
  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 36 36" className={`${sz} -rotate-90`}>
        <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          fill="none" stroke="#e5e7eb" strokeWidth="3.5"/>
        <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          fill="none" stroke={color} strokeWidth="3.5" strokeDasharray={`${score}, 100`}
          strokeLinecap="round"/>
      </svg>
      <span className={`${textSz} font-bold -mt-1`} style={{ color }}>{score}</span>
      <span className="text-xs text-gray-400">/ 100</span>
    </div>
  );
}

function ScoreBar({ label, score, max = 100 }) {
  const pct = Math.min(100, Math.round((score / max) * 100));
  const color = pct >= 80 ? "bg-green-500" : pct >= 50 ? "bg-yellow-400" : "bg-red-400";
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-gray-600 w-24 shrink-0">{label}</span>
      <div className="flex-1 bg-gray-100 rounded-full h-2">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${pct}%` }}/>
      </div>
      <span className="text-xs font-bold text-gray-700 w-8 text-right">{score}</span>
    </div>
  );
}

function StatusDot({ ok, label }) {
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium ${ok ? "text-green-700" : "text-red-600"}`}>
      <span className={`w-2 h-2 rounded-full ${ok ? "bg-green-500" : "bg-red-500"}`}/>
      {label}
    </span>
  );
}

function CodeBlock({ code }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="relative group">
      <pre className="bg-gray-900 text-green-300 text-xs p-3 rounded-lg overflow-x-auto whitespace-pre-wrap leading-relaxed">{code}</pre>
      <button onClick={() => { navigator.clipboard.writeText(code); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
        className="absolute top-2 right-2 text-xs bg-gray-700 hover:bg-gray-600 text-gray-300 px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity">
        {copied ? "✓ Copied" : "Copy"}
      </button>
    </div>
  );
}

function IssueCard({ issue }) {
  if (typeof issue === "string") return (
    <div className="flex gap-2 p-2 text-sm text-red-700 bg-red-50 rounded border-l-4 border-red-400">
      <span>⚠</span><span>{issue}</span>
    </div>
  );
  const p = issue.priority || "medium";
  return (
    <div className={`rounded-lg px-3 py-2 text-sm ${PRIORITY_STYLE[p]}`}>
      <div className="flex items-center gap-2 mb-0.5">
        <Badge priority={p} />
        <span className="font-semibold text-gray-800">{issue.element}</span>
      </div>
      <p className="text-gray-700">{issue.problem}</p>
      {issue.fix && <p className="text-xs text-gray-500 mt-1">→ Fix: {issue.fix}</p>}
    </div>
  );
}

// ── Tab: Overview ──────────────────────────────────────────────────────────────

function OverviewTab({ techData, pages }) {
  if (!techData) return <p className="text-gray-500">No data available.</p>;

  const criticalCount = techData.summary?.critical || 0;
  const highCount     = techData.summary?.high || 0;
  const totalIssues   = techData.issues?.length || 0;
  const avgScore = pages?.length
    ? Math.round(pages.reduce((s, p) => s + (p.score || 0), 0) / pages.length)
    : 0;

  return (
    <div className="space-y-6">
      {/* Score cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: "Technical Score",   val: techData.score || 0,    unit: "/100", color: techData.score >= 80 ? "green" : techData.score >= 50 ? "yellow" : "red" },
          { label: "Avg On-Page Score", val: avgScore,               unit: "/100", color: avgScore >= 80 ? "green" : avgScore >= 50 ? "yellow" : "red" },
          { label: "Pages Crawled",     val: techData.total_pages_crawled, unit: " pages", color: "blue" },
          { label: "Critical Issues",   val: criticalCount,          unit: " critical", color: criticalCount > 0 ? "red" : "green" },
        ].map(item => (
          <div key={item.label} className="text-center p-4 bg-white rounded-xl border border-gray-200 shadow-sm">
            <p className="text-xs text-gray-500 font-medium mb-2">{item.label}</p>
            <p className={`text-3xl font-bold text-${item.color}-600`}>{item.val}</p>
            <p className="text-xs text-gray-400 mt-0.5">{item.unit}</p>
          </div>
        ))}
      </div>

      {/* Status grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: "HTTPS",      ok: techData.https_enabled },
          { label: "robots.txt", ok: techData.robots_txt_found },
          { label: "Sitemap",    ok: techData.sitemap?.found },
          { label: "Sitemap URLs", ok: true, val: techData.sitemap?.url_count || 0 },
        ].map(item => (
          <div key={item.label} className={`p-3 rounded-xl border-2 text-center ${item.ok ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50"}`}>
            <p className="text-xs text-gray-500">{item.label}</p>
            <p className={`font-bold mt-1 ${item.ok ? "text-green-700" : "text-red-600"}`}>
              {item.val !== undefined ? item.val : item.ok ? "✅ Yes" : "❌ No"}
            </p>
          </div>
        ))}
      </div>

      {/* Issue summary counts */}
      <div>
        <h4 className="font-semibold text-gray-800 mb-3">Issue Summary ({totalIssues} total)</h4>
        <div className="grid grid-cols-4 gap-2">
          {[
            { label: "Critical", count: techData.summary?.critical || 0, color: "red" },
            { label: "High",     count: techData.summary?.high || 0,     color: "orange" },
            { label: "Medium",   count: techData.summary?.medium || 0,   color: "yellow" },
            { label: "Low",      count: techData.summary?.low || 0,      color: "green" },
          ].map(item => (
            <div key={item.label} className={`text-center p-3 rounded-xl bg-${item.color}-50 border border-${item.color}-200`}>
              <p className={`text-2xl font-bold text-${item.color}-600`}>{item.count}</p>
              <p className={`text-xs text-${item.color}-700 font-medium`}>{item.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Top critical issues preview */}
      {techData.issues?.filter(i => i.priority === "critical" || i.priority === "high").length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-800 mb-3">Top Issues to Fix First</h4>
          <div className="space-y-2">
            {techData.issues.filter(i => i.priority === "critical" || i.priority === "high").map((issue, i) => (
              <IssueCard key={i} issue={issue} />
            ))}
          </div>
        </div>
      )}

      {/* Page scores overview */}
      {pages?.length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-800 mb-3">All Pages — Score Overview</h4>
          <div className="space-y-2">
            {pages.map((p, i) => (
              <div key={i} className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg border border-gray-100">
                <span className={`text-sm font-bold w-8 text-center ${p.score >= 80 ? "text-green-600" : p.score >= 50 ? "text-yellow-600" : "text-red-600"}`}>
                  {p.score}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-gray-500 truncate">{p.url}</p>
                  <p className="text-xs font-medium text-gray-700 truncate">{p.current?.title || "— No title —"}</p>
                </div>
                <span className="text-xs px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded">{p.page_type}</span>
                <span className="text-xs text-red-500">{p.issues?.length || 0} issues</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Tab: Technical SEO ─────────────────────────────────────────────────────────

function TechnicalTab({ data }) {
  if (!data) return <p className="text-gray-500">No technical data available.</p>;
  return (
    <div className="space-y-6">
      <div className="flex items-start gap-6 flex-wrap">
        <ScoreCircle score={data.score || 0} />
        <div className="flex-1 min-w-0 space-y-2">
          <ScoreBar label="Technical Score" score={data.score || 0} />
          <div className="grid grid-cols-2 gap-2 mt-3">
            <StatusDot ok={data.https_enabled}        label="HTTPS Enabled" />
            <StatusDot ok={data.robots_txt_found}     label="robots.txt Found" />
            <StatusDot ok={!!data.sitemap?.found}     label={`Sitemap (${data.sitemap?.url_count || 0} URLs)`} />
            <StatusDot ok={data.total_pages_crawled > 1} label={`${data.total_pages_crawled} Pages Crawled`} />
          </div>
        </div>
      </div>

      <div>
        <h4 className="font-semibold text-gray-800 mb-3">All Issues ({data.issues?.length || 0})</h4>
        <div className="space-y-2">
          {(data.issues || []).map((issue, i) => <IssueCard key={i} issue={issue} />)}
        </div>
      </div>

      {data.recommendations?.length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-800 mb-2">What's Working ✅</h4>
          <ul className="space-y-1.5">
            {data.recommendations.map((r, i) => (
              <li key={i} className="flex gap-2 text-sm text-green-700 bg-green-50 rounded p-2">
                <span>✓</span><span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {data.robots_txt_content && (
        <div>
          <h4 className="font-semibold text-gray-800 mb-2">robots.txt Content</h4>
          <CodeBlock code={data.robots_txt_content} />
        </div>
      )}
    </div>
  );
}

// ── Tab: All Pages ─────────────────────────────────────────────────────────────

function AllPagesTab({ pages }) {
  const [expanded, setExpanded] = useState(null);
  if (!pages?.length) return <p className="text-gray-500">No page data available.</p>;

  return (
    <div className="space-y-4">
      {/* Summary table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="bg-gray-800 text-white">
              <th className="text-left p-2 rounded-tl-lg">#</th>
              <th className="text-left p-2">Page URL</th>
              <th className="text-left p-2">Type</th>
              <th className="text-center p-2">Score</th>
              <th className="text-left p-2">Suggested Slug</th>
              <th className="text-center p-2">Title</th>
              <th className="text-center p-2">Meta</th>
              <th className="text-center p-2">H1</th>
              <th className="text-center p-2">Schema</th>
              <th className="text-center p-2 rounded-tr-lg">Issues</th>
            </tr>
          </thead>
          <tbody>
            {pages.map((p, i) => {
              const scoreColor = p.score >= 80 ? "text-green-600" : p.score >= 50 ? "text-yellow-600" : "text-red-600";
              const hasTitle    = !!p.current?.title;
              const hasMeta     = !!p.current?.meta_description;
              const hasH1       = p.current?.h1?.length > 0;
              const hasSchema   = p.current?.schema_count > 0;
              const isOpen = expanded === i;
              return [
                <tr key={`row-${i}`}
                  onClick={() => setExpanded(isOpen ? null : i)}
                  className={`border-b border-gray-100 cursor-pointer transition-colors ${isOpen ? "bg-blue-50" : "hover:bg-gray-50"}`}>
                  <td className="p-2 text-gray-400">{i + 1}</td>
                  <td className="p-2 max-w-xs">
                    <p className="text-gray-500 truncate">{p.url}</p>
                    <p className="text-gray-800 font-medium truncate">{p.current?.title || "— no title —"}</p>
                  </td>
                  <td className="p-2">
                    <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">{p.page_type}</span>
                  </td>
                  <td className="p-2 text-center">
                    <span className={`text-sm font-bold ${scoreColor}`}>{p.score}</span>
                  </td>
                  <td className="p-2 font-mono text-blue-600">{p.suggestions?.slug || "/"}</td>
                  <td className="p-2 text-center">{hasTitle ? "✅" : "❌"}</td>
                  <td className="p-2 text-center">{hasMeta  ? "✅" : "❌"}</td>
                  <td className="p-2 text-center">{hasH1    ? "✅" : "❌"}</td>
                  <td className="p-2 text-center">{hasSchema ? "✅" : "❌"}</td>
                  <td className="p-2 text-center">
                    <span className={`font-bold ${p.issues?.length > 3 ? "text-red-600" : "text-yellow-600"}`}>
                      {p.issues?.length || 0}
                    </span>
                  </td>
                </tr>,
                isOpen && (
                  <tr key={`detail-${i}`}>
                    <td colSpan={10} className="bg-blue-50 p-0">
                      <PageDeepDive page={p} />
                    </td>
                  </tr>
                ),
              ];
            })}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-gray-400 text-center">Click any row to expand full page analysis</p>
    </div>
  );
}

function PageDeepDive({ page }) {
  const [subTab, setSubTab] = useState("analysis");
  const p = page;

  return (
    <div className="border-t border-blue-200 p-4 space-y-4">
      {/* Sub-tabs */}
      <div className="flex gap-1 border-b border-blue-200 overflow-x-auto">
        {["analysis", "suggestions", "local-seo", "schema", "keywords", "dev-hints"].map(t => (
          <button key={t} onClick={() => setSubTab(t)}
            className={`px-3 py-1.5 text-xs font-medium whitespace-nowrap border-b-2 -mb-px transition-colors capitalize ${
              subTab === t ? "border-blue-500 text-blue-600" : "border-transparent text-gray-500 hover:text-gray-700"
            }`}>
            {t === "dev-hints" ? "Dev Hints" : t === "local-seo" ? "📍 Local SEO" : t}
          </button>
        ))}
      </div>

      {/* Analysis */}
      {subTab === "analysis" && (
        <div className="space-y-4">
          {/* Score breakdown */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h5 className="text-xs font-semibold text-gray-500 uppercase mb-2">Score Breakdown</h5>
              <div className="space-y-1.5">
                {Object.entries(p.scores || {}).filter(([k]) => k !== "overall").map(([k, v]) => (
                  <ScoreBar key={k} label={k.charAt(0).toUpperCase() + k.slice(1)} score={v} />
                ))}
              </div>
            </div>
            <div>
              <h5 className="text-xs font-semibold text-gray-500 uppercase mb-2">Page Details</h5>
              <dl className="space-y-1 text-xs">
                <div className="flex gap-2"><dt className="text-gray-500 w-24">Type:</dt><dd className="font-medium">{p.page_type}</dd></div>
                <div className="flex gap-2"><dt className="text-gray-500 w-24">Title:</dt><dd className="font-medium">{p.current?.title_length || 0} chars {p.current?.title_length > 65 ? "⚠ too long" : p.current?.title_length < 30 ? "⚠ too short" : "✅"}</dd></div>
                <div className="flex gap-2"><dt className="text-gray-500 w-24">Meta:</dt><dd className="font-medium">{p.current?.meta_length || 0} chars {p.current?.meta_length > 165 ? "⚠ too long" : p.current?.meta_length < 100 ? "⚠ too short" : "✅"}</dd></div>
                <div className="flex gap-2"><dt className="text-gray-500 w-24">Word count:</dt><dd className="font-medium">{p.current?.word_count}</dd></div>
                <div className="flex gap-2"><dt className="text-gray-500 w-24">H1 count:</dt><dd className="font-medium">{p.current?.h1?.length || 0} {p.current?.h1?.length > 1 ? "⚠ multiple" : ""}</dd></div>
                <div className="flex gap-2"><dt className="text-gray-500 w-24">H2 count:</dt><dd className="font-medium">{p.current?.h2?.length || 0}</dd></div>
                <div className="flex gap-2"><dt className="text-gray-500 w-24">Schema:</dt><dd className="font-medium">{p.current?.schema_count || 0} found {p.current?.schema_types?.length ? `(${p.current.schema_types.join(", ")})` : ""}</dd></div>
                <div className="flex gap-2"><dt className="text-gray-500 w-24">Canonical:</dt><dd className="font-medium">{p.current?.canonical ? "✅ Set" : "❌ Missing"}</dd></div>
                <div className="flex gap-2"><dt className="text-gray-500 w-24">OG Tags:</dt><dd className="font-medium">{p.current?.og_title ? "✅ Set" : "❌ Missing"}</dd></div>
                <div className="flex gap-2"><dt className="text-gray-500 w-24">Images:</dt><dd className="font-medium">{p.current?.images_without_alt || 0} missing alt</dd></div>
                <div className="flex gap-2"><dt className="text-gray-500 w-24">Int. links:</dt><dd className="font-medium">{p.current?.internal_links_count || 0}</dd></div>
              </dl>
            </div>
          </div>

          {/* H-tags structure */}
          {(p.current?.h1?.length > 0 || p.current?.h2?.length > 0 || p.current?.h3?.length > 0) && (
            <div>
              <h5 className="text-xs font-semibold text-gray-500 uppercase mb-2">Heading Structure</h5>
              <div className="space-y-1 text-xs font-mono">
                {p.current?.h1?.map((h, i) => <div key={i} className="text-purple-700 bg-purple-50 px-2 py-0.5 rounded">H1: {h}</div>)}
                {p.current?.h2?.map((h, i) => <div key={i} className="text-blue-700 bg-blue-50 px-2 py-0.5 rounded ml-3">H2: {h}</div>)}
                {p.current?.h3?.map((h, i) => <div key={i} className="text-green-700 bg-green-50 px-2 py-0.5 rounded ml-6">H3: {h}</div>)}
              </div>
            </div>
          )}

          {/* Issues */}
          <div>
            <h5 className="text-xs font-semibold text-gray-500 uppercase mb-2">Issues ({p.issues?.length || 0})</h5>
            <div className="space-y-2">
              {(p.issues || []).map((issue, i) => <IssueCard key={i} issue={issue} />)}
            </div>
          </div>
        </div>
      )}

      {/* Suggestions */}
      {subTab === "suggestions" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[
              { label: "Suggested Title",       val: p.suggestions?.title,            note: "50-60 chars" },
              { label: "Suggested Meta",        val: p.suggestions?.meta_description, note: "150-160 chars" },
              { label: "Suggested H1",          val: p.suggestions?.h1,               note: "One per page" },
              { label: "Suggested URL Slug",    val: p.suggestions?.slug,             note: "Lowercase, hyphens", mono: true },
              { label: "Canonical URL",         val: p.suggestions?.canonical,        note: "Exact URL", mono: true },
            ].map(item => item.val && (
              <div key={item.label} className="bg-white border border-gray-200 rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold text-blue-600">{item.label}</span>
                  <span className="text-xs text-gray-400">{item.note}</span>
                </div>
                <p className={`text-sm text-gray-800 ${item.mono ? "font-mono" : ""}`}>{item.val}</p>
              </div>
            ))}
          </div>

          {/* Content improvements */}
          {p.suggestions?.content_improvements?.length > 0 && (
            <div>
              <h5 className="text-xs font-semibold text-gray-500 uppercase mb-2">Content Improvements</h5>
              <div className="space-y-2">
                {p.suggestions.content_improvements.map((c, i) => (
                  <div key={i} className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-sm">
                    <p className="font-semibold text-yellow-800">⚠ {c.issue}</p>
                    <p className="text-yellow-700 mt-1">Fix: {c.fix}</p>
                    {c.example && <p className="text-xs text-gray-500 mt-1 italic">{c.example}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Internal link suggestions */}
          {p.suggestions?.internal_link_suggestions?.length > 0 && (
            <div>
              <h5 className="text-xs font-semibold text-gray-500 uppercase mb-2">Internal Link Suggestions</h5>
              <div className="overflow-x-auto">
                <table className="w-full text-xs border-collapse">
                  <thead><tr className="bg-gray-100">
                    <th className="text-left p-2">Anchor Text</th>
                    <th className="text-left p-2">Target URL</th>
                    <th className="text-left p-2">Reason</th>
                  </tr></thead>
                  <tbody>
                    {p.suggestions.internal_link_suggestions.map((l, i) => (
                      <tr key={i} className="border-t border-gray-100">
                        <td className="p-2 text-blue-600">{l.anchor}</td>
                        <td className="p-2 font-mono text-gray-600">{l.target}</td>
                        <td className="p-2 text-gray-500">{l.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Image alts */}
          {p.suggestions?.image_alts?.length > 0 && (
            <div>
              <h5 className="text-xs font-semibold text-gray-500 uppercase mb-2">
                Images Missing Alt ({p.suggestions.image_alts.length})
              </h5>
              {p.suggestions.image_alts.map((img, i) => (
                <div key={i} className="bg-yellow-50 border border-yellow-200 rounded p-2 mb-1 text-xs">
                  <p className="text-gray-500 truncate">{img.src}</p>
                  <p className="text-yellow-800 font-medium">Suggested alt: "{img.suggested_alt}"</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Schema */}
      {subTab === "schema" && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs font-semibold text-gray-500 mb-1">Currently Found</p>
              {p.current?.schema_count > 0
                ? p.current.schema_types.map((t, i) => <span key={i} className="inline-block px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded mr-1 mb-1">{t}</span>)
                : <p className="text-red-600 text-sm">❌ No schema markup found</p>
              }
            </div>
            <div className="bg-blue-50 rounded-lg p-3">
              <p className="text-xs font-semibold text-blue-600 mb-1">Recommended Type</p>
              <p className="text-sm font-bold text-blue-800">{p.suggestions?.schema_json_ld?.["@type"] || "WebPage"}</p>
              <p className="text-xs text-blue-600 mt-1">For {p.page_type} page</p>
            </div>
          </div>

          {p.suggestions?.schema_json_ld && (
            <div>
              <h5 className="text-xs font-semibold text-gray-500 uppercase mb-2">
                Recommended Schema JSON-LD — Copy & paste in &lt;head&gt;
              </h5>
              <CodeBlock code={`<script type="application/ld+json">\n${JSON.stringify(p.suggestions.schema_json_ld, null, 2)}\n</script>`} />
            </div>
          )}
        </div>
      )}

      {/* Keywords */}
      {subTab === "keywords" && (
        <div className="space-y-3">
          <h5 className="text-xs font-semibold text-gray-500 uppercase">Extracted Keywords (Top 10)</h5>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead><tr className="bg-gray-100">
                <th className="text-left p-2">#</th>
                <th className="text-left p-2">Keyword</th>
                <th className="text-right p-2">Frequency</th>
                <th className="text-center p-2">In Title</th>
                <th className="text-center p-2">In H1</th>
              </tr></thead>
              <tbody>
                {(p.keywords || []).map(([kw, cnt], i) => {
                  const inTitle = p.current?.title?.toLowerCase().includes(kw.toLowerCase());
                  const inH1 = p.current?.h1?.some(h => h.toLowerCase().includes(kw.toLowerCase()));
                  return (
                    <tr key={i} className={`border-t border-gray-100 ${i === 0 ? "bg-blue-50" : ""}`}>
                      <td className="p-2 text-gray-400">{i + 1}</td>
                      <td className="p-2 font-medium">{kw}</td>
                      <td className="p-2 text-right text-gray-600">{cnt}×</td>
                      <td className="p-2 text-center">{inTitle ? "✅" : "❌"}</td>
                      <td className="p-2 text-center">{inH1 ? "✅" : "❌"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {p.readability && (
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs font-semibold text-gray-500 mb-1">Readability</p>
              <p className="text-sm font-bold">{p.readability.grade} <span className="font-normal text-gray-500">({p.readability.score}/100)</span></p>
              <p className="text-xs text-gray-500">Avg sentence: {p.readability.avg_sentence_length} words · {p.readability.sentence_count} sentences</p>
            </div>
          )}
        </div>
      )}

      {/* Local SEO */}
      {subTab === "local-seo" && (
        <div className="space-y-4">
          {(() => {
            const local = p.suggestions?.local_seo;
            if (!local) return <p className="text-gray-500 text-sm">No local SEO data.</p>;
            return (
              <>
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <p className="text-xs font-semibold text-green-700 mb-1">Cities Found in Content</p>
                    {local.cities_found_in_content?.length > 0
                      ? local.cities_found_in_content.map((c,i) => <span key={i} className="inline-block px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded mr-1">✅ {c}</span>)
                      : <p className="text-xs text-red-600">❌ None — no city targeting</p>}
                  </div>
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p className="text-xs font-semibold text-red-700 mb-1">Missing Cities</p>
                    {local.cities_missing?.map((c,i) => <span key={i} className="inline-block px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded mr-1">{c}</span>)}
                  </div>
                </div>

                {local.priority_keywords?.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-gray-600 mb-2">🎯 Target Keywords (Local)</p>
                    <div className="flex flex-wrap gap-1.5">
                      {local.priority_keywords.map((kw,i) => <span key={i} className="px-2.5 py-1 bg-blue-50 border border-blue-200 text-blue-700 text-xs rounded-full">{kw}</span>)}
                    </div>
                  </div>
                )}

                {local.gmb_checklist?.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-gray-600 mb-2">📍 Google Business Profile Checklist</p>
                    <ul className="space-y-1.5">
                      {local.gmb_checklist.map((item,i) => (
                        <li key={i} className="flex items-start gap-2 text-xs text-gray-700 bg-gray-50 rounded p-2">
                          <span className="text-gray-400 mt-0.5">☐</span><span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {local.city_landing_pages?.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-gray-600 mb-2">🏙️ Recommended City Landing Pages</p>
                    <div className="space-y-3">
                      {local.city_landing_pages.map((cp,i) => (
                        <div key={i} className="bg-white border border-gray-200 rounded-lg p-3 text-xs">
                          <p className="font-bold text-blue-600 font-mono">{cp.page}</p>
                          <p className="text-gray-600 mt-1"><span className="font-semibold">Title:</span> {cp.title}</p>
                          <p className="text-gray-600"><span className="font-semibold">Meta:</span> {cp.meta}</p>
                          <p className="text-gray-600"><span className="font-semibold">H1:</span> {cp.h1}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            );
          })()}
        </div>
      )}

      {/* Dev hints */}
      {subTab === "dev-hints" && (
        <div className="space-y-4">
          {(p.suggestions?.developer_hints || []).map((hint, i) => (
            <div key={i} className="space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <Badge priority={hint.priority} label={hint.priority} />
                <span className="text-xs font-bold text-gray-700">{hint.type}</span>
                <span className="text-xs text-gray-400">{hint.section}</span>
              </div>
              <p className="text-xs text-gray-600">{hint.description}</p>
              <CodeBlock code={hint.code} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Tab: Schema Report ─────────────────────────────────────────────────────────

function SchemaTab({ pages }) {
  const [selectedPage, setSelectedPage] = useState(0);
  if (!pages?.length) return <p className="text-gray-500">No page data.</p>;

  const schemaStats = pages.reduce((acc, p) => {
    acc.total++;
    if (p.current?.schema_count > 0) acc.withSchema++;
    else acc.missing++;
    return acc;
  }, { total: 0, withSchema: 0, missing: 0 });

  const page = pages[selectedPage];

  return (
    <div className="space-y-5">
      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="text-center p-3 bg-gray-50 rounded-xl border">
          <p className="text-2xl font-bold text-gray-700">{schemaStats.total}</p>
          <p className="text-xs text-gray-500">Total Pages</p>
        </div>
        <div className="text-center p-3 bg-green-50 rounded-xl border border-green-200">
          <p className="text-2xl font-bold text-green-600">{schemaStats.withSchema}</p>
          <p className="text-xs text-green-700">Have Schema</p>
        </div>
        <div className="text-center p-3 bg-red-50 rounded-xl border border-red-200">
          <p className="text-2xl font-bold text-red-600">{schemaStats.missing}</p>
          <p className="text-xs text-red-700">Missing Schema</p>
        </div>
      </div>

      {/* Page list */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Select Page</h4>
          <div className="space-y-1 max-h-80 overflow-y-auto pr-1">
            {pages.map((p, i) => (
              <button key={i} onClick={() => setSelectedPage(i)}
                className={`w-full text-left px-3 py-2 rounded-lg border text-xs transition-colors ${
                  selectedPage === i ? "border-blue-400 bg-blue-50" : "border-gray-200 hover:bg-gray-50"
                }`}>
                <div className="flex items-center justify-between">
                  <span className="truncate text-gray-700 font-medium">{p.current?.title || p.url}</span>
                  {p.current?.schema_count > 0
                    ? <span className="ml-2 px-1.5 py-0.5 bg-green-100 text-green-700 rounded shrink-0">✅ {p.current.schema_count} schema</span>
                    : <span className="ml-2 px-1.5 py-0.5 bg-red-100 text-red-700 rounded shrink-0">❌ Missing</span>
                  }
                </div>
                <p className="text-gray-400 truncate mt-0.5">{p.url}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Selected page schema detail */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">{page?.current?.title || page?.url}</h4>
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Page type:</span>
              <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-medium">{page?.page_type}</span>
              <span className="text-xs text-gray-500">Recommended:</span>
              <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-medium">
                {page?.suggestions?.schema_json_ld?.["@type"] || "WebPage"}
              </span>
            </div>

            {page?.current?.schema_count > 0 ? (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                <p className="text-xs font-semibold text-green-700 mb-1">✅ Schema Found</p>
                <div className="flex flex-wrap gap-1">
                  {page.current.schema_types.map((t, i) => (
                    <span key={i} className="px-2 py-0.5 bg-green-100 text-green-800 rounded text-xs">{t}</span>
                  ))}
                </div>
              </div>
            ) : (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
                ❌ No schema markup found on this page. Add the recommended schema below.
              </div>
            )}

            {page?.suggestions?.schema_json_ld && (
              <div>
                <p className="text-xs font-semibold text-gray-600 mb-1">📋 Recommended JSON-LD (copy to &lt;head&gt;)</p>
                <CodeBlock code={`<script type="application/ld+json">\n${JSON.stringify(page.suggestions.schema_json_ld, null, 2)}\n</script>`} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Tab: PageSpeed ────────────────────────────────────────────────────────────

const CWV_COLORS = { good: "text-green-600 bg-green-50 border-green-200", "needs-improvement": "text-yellow-600 bg-yellow-50 border-yellow-200", poor: "text-red-600 bg-red-50 border-red-200", "N/A": "text-gray-400 bg-gray-50 border-gray-200" };

function CWVCard({ metric }) {
  const status = metric.status || "N/A";
  const colorClass = CWV_COLORS[status] || CWV_COLORS["N/A"];
  const icon = status === "good" ? "✅" : status === "needs-improvement" ? "⚠️" : status === "poor" ? "❌" : "—";
  return (
    <div className={`rounded-xl border p-3 ${colorClass}`}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-semibold">{metric.label}</span>
        <span>{icon}</span>
      </div>
      <p className="text-xl font-bold">{metric.value}</p>
      <p className="text-xs opacity-70 mt-0.5 capitalize">{status.replace("-", " ")}</p>
      <p className="text-xs opacity-60 mt-1 leading-tight">{metric.description}</p>
    </div>
  );
}

function PageSpeedPanel({ data, strategy }) {
  if (!data || data.error) return (
    <div className="bg-gray-50 rounded-xl p-4 text-sm text-gray-500">
      {data?.error || "PageSpeed data not available for this audit."}
    </div>
  );

  const scores = data.scores || {};
  const cwv = data.core_web_vitals || {};
  const scoreColor = (s) => s >= 90 ? "text-green-600" : s >= 50 ? "text-yellow-600" : "text-red-600";
  const scoreBg   = (s) => s >= 90 ? "bg-green-50 border-green-200" : s >= 50 ? "bg-yellow-50 border-yellow-200" : "bg-red-50 border-red-200";

  return (
    <div className="space-y-5">
      {/* Lighthouse scores */}
      <div>
        <h5 className="text-xs font-semibold text-gray-500 uppercase mb-3 flex items-center gap-2">
          <span>🔦</span> Lighthouse Scores ({strategy})
        </h5>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Performance",    val: scores.performance },
            { label: "SEO",            val: scores.seo },
            { label: "Accessibility",  val: scores.accessibility },
            { label: "Best Practices", val: scores.best_practices },
          ].map(item => (
            <div key={item.label} className={`text-center p-3 rounded-xl border ${scoreBg(item.val)}`}>
              <p className="text-xs text-gray-500 mb-1">{item.label}</p>
              <p className={`text-3xl font-bold ${scoreColor(item.val)}`}>{item.val ?? "—"}</p>
              <p className="text-xs text-gray-400">/100</p>
            </div>
          ))}
        </div>
      </div>

      {/* Core Web Vitals */}
      <div>
        <h5 className="text-xs font-semibold text-gray-500 uppercase mb-3 flex items-center gap-2">
          <span>📐</span> Core Web Vitals
        </h5>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {Object.values(cwv).map((m, i) => <CWVCard key={i} metric={m} />)}
        </div>
      </div>

      {/* Opportunities */}
      {data.opportunities?.length > 0 && (
        <div>
          <h5 className="text-xs font-semibold text-gray-500 uppercase mb-3">⚡ Speed Opportunities</h5>
          <div className="space-y-2">
            {data.opportunities.map((opp, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-orange-50 border border-orange-200 rounded-lg">
                <span className="text-orange-500 mt-0.5 shrink-0">⚠</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-gray-800">{opp.title}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{opp.description}</p>
                </div>
                {opp.display_value && (
                  <span className="text-xs font-bold text-orange-700 whitespace-nowrap shrink-0">{opp.display_value}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SEO audits from Lighthouse */}
      {data.seo_audits && Object.keys(data.seo_audits).length > 0 && (
        <div>
          <h5 className="text-xs font-semibold text-gray-500 uppercase mb-3">🔍 Google SEO Audits</h5>
          <div className="overflow-x-auto">
            <table className="w-full text-xs border-collapse">
              <thead><tr className="bg-gray-100">
                <th className="text-left p-2">Check</th>
                <th className="text-center p-2">Score</th>
                <th className="text-left p-2">Details</th>
              </tr></thead>
              <tbody>
                {Object.values(data.seo_audits).map((a, i) => (
                  <tr key={i} className="border-t border-gray-100">
                    <td className="p-2 font-medium text-gray-700">{a.title}</td>
                    <td className="p-2 text-center">
                      {a.score === null ? "—" : (
                        <span className={`font-bold ${a.score >= 90 ? "text-green-600" : a.score >= 50 ? "text-yellow-600" : "text-red-600"}`}>
                          {a.score >= 90 ? "✅" : a.score >= 50 ? "⚠️" : "❌"}
                        </span>
                      )}
                    </td>
                    <td className="p-2 text-gray-500">{a.display_value || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function PageSpeedTab({ pagespeed }) {
  const [strategy, setStrategy] = useState("mobile");
  if (!pagespeed) return (
    <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 text-center">
      <p className="text-2xl mb-2">⏳</p>
      <p className="text-sm font-semibold text-blue-700">PageSpeed data not available</p>
      <p className="text-xs text-blue-600 mt-1">Run a new audit to get Google PageSpeed Insights data</p>
    </div>
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="font-semibold text-gray-800 flex items-center gap-2">
          <span>🚀</span> Google PageSpeed Insights
        </h4>
        <div className="flex gap-1 p-1 bg-gray-100 rounded-lg">
          {["mobile", "desktop"].map(s => (
            <button key={s} onClick={() => setStrategy(s)}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors capitalize ${strategy === s ? "bg-white shadow text-blue-600" : "text-gray-500"}`}>
              {s === "mobile" ? "📱 Mobile" : "🖥️ Desktop"}
            </button>
          ))}
        </div>
      </div>
      <PageSpeedPanel data={pagespeed[strategy]} strategy={strategy} />
    </div>
  );
}

// ── Tab: AI Advisor ────────────────────────────────────────────────────────────

function AIAdvisorTab({ aiRec }) {
  if (!aiRec) return (
    <div className="bg-purple-50 border border-purple-200 rounded-xl p-6 text-center">
      <p className="text-3xl mb-2">🤖</p>
      <p className="text-sm font-semibold text-purple-700">AI recommendations not available</p>
      <p className="text-xs text-purple-600 mt-1">Add your ANTHROPIC_API_KEY to the backend .env file and run a new audit</p>
      <div className="mt-3 bg-white rounded-lg p-3 text-left">
        <p className="text-xs font-mono text-gray-600">1. Open: seo-ai-agent/backend/.env</p>
        <p className="text-xs font-mono text-gray-600">2. Set: ANTHROPIC_API_KEY=sk-ant-...</p>
        <p className="text-xs font-mono text-gray-600">3. Get key: console.anthropic.com</p>
      </div>
    </div>
  );
  if (aiRec.error) return (
    <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
      ⚠ AI Error: {aiRec.error}
    </div>
  );

  const gradeColor = { A: "text-green-600", B: "text-blue-600", C: "text-yellow-600", D: "text-orange-600", F: "text-red-600" };
  const grade = aiRec.seo_grade || "?";

  return (
    <div className="space-y-5">
      {/* Grade + Summary */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-xl p-5">
        <div className="flex items-start gap-4">
          <div className="text-center shrink-0">
            <p className={`text-5xl font-black ${gradeColor[grade] || "text-gray-700"}`}>{grade}</p>
            <p className="text-xs text-gray-500 font-medium">SEO Grade</p>
          </div>
          <div>
            <h4 className="font-bold text-gray-900 mb-1 flex items-center gap-2">
              <span>🤖</span> AI Executive Summary
            </h4>
            <p className="text-sm text-gray-700 leading-relaxed">{aiRec.executive_summary}</p>
          </div>
        </div>
      </div>

      {/* Top 5 Actions */}
      {aiRec.top_5_actions?.length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
            🎯 Top 5 Priority Actions
          </h4>
          <div className="space-y-3">
            {aiRec.top_5_actions.map((action, i) => (
              <div key={i} className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
                <div className="flex items-start gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm shrink-0 ${
                    i === 0 ? "bg-red-500" : i === 1 ? "bg-orange-500" : i === 2 ? "bg-yellow-500" : "bg-blue-400"
                  }`}>{i + 1}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span className="text-sm font-semibold text-gray-900">{action.element}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        action.impact === "high" ? "bg-red-100 text-red-700" : action.impact === "medium" ? "bg-yellow-100 text-yellow-700" : "bg-green-100 text-green-700"
                      }`}>
                        {action.impact} impact
                      </span>
                      <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full">{action.effort}</span>
                      {action.pages_affected && <span className="text-xs text-gray-400">{action.pages_affected}</span>}
                    </div>
                    <p className="text-sm text-gray-700">{action.action}</p>
                    {action.why && <p className="text-xs text-blue-600 mt-1 italic">Why: {action.why}</p>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Wins */}
      {aiRec.quick_wins?.length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
            ⚡ Quick Wins (under 30 min each)
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {aiRec.quick_wins.map((win, i) => (
              <div key={i} className="flex items-start gap-2 bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-green-800">
                <span className="shrink-0 mt-0.5">✓</span>
                <span>{win}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 30-day roadmap */}
      {aiRec["30_day_roadmap"] && (
        <div>
          <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
            📅 30-Day Action Roadmap
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[
              { key: "week_1_critical", label: "Week 1 — Critical", color: "red" },
              { key: "week_2_onpage",   label: "Week 2 — On-Page",  color: "orange" },
              { key: "week_3_content",  label: "Week 3 — Content",  color: "yellow" },
              { key: "week_4_technical",label: "Week 4 — Technical",color: "blue" },
            ].map(({ key, label, color }) => {
              const items = aiRec["30_day_roadmap"][key] || [];
              return (
                <div key={key} className={`border-l-4 border-${color}-400 pl-4`}>
                  <h5 className={`text-sm font-bold text-${color}-700 mb-2`}>{label}</h5>
                  <ul className="space-y-1">
                    {items.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-gray-700">
                        <span className="text-gray-400 mt-0.5 shrink-0">☐</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Performance + Impact */}
      {(aiRec.performance_insights || aiRec.estimated_impact) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {aiRec.performance_insights && (
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <h5 className="text-xs font-bold text-blue-700 mb-1">🚀 Performance Insights</h5>
              <p className="text-sm text-blue-800">{aiRec.performance_insights}</p>
            </div>
          )}
          {aiRec.estimated_impact && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-4">
              <h5 className="text-xs font-bold text-green-700 mb-1">📈 Estimated Impact</h5>
              <p className="text-sm text-green-800">{aiRec.estimated_impact}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Tab: Download ──────────────────────────────────────────────────────────────

function DownloadTab({ reportFiles, onDownload, token, apiBase }) {
  const downloadFile = (file) => {
    fetch(`${apiBase}${file.download_url}`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.blob()).then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url; a.download = file.name; a.click();
        URL.revokeObjectURL(url);
      });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="font-semibold text-gray-800">Generated Word Documents</h4>
        <button onClick={onDownload} className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg font-medium transition-colors">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
          </svg>
          Download All (.zip)
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {(reportFiles || []).map(file => (
          <div key={file.name} className="flex items-center justify-between p-4 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center text-xl">📄</div>
              <div>
                <p className="text-sm font-medium text-gray-900">
                  {file.name.replace(/^\d+_/, "").replace(/_/g, " ").replace(".docx", "")}
                </p>
                <p className="text-xs text-gray-500">{file.size_kb} KB · Word (.docx)</p>
              </div>
            </div>
            <button onClick={() => downloadFile(file)} className="px-3 py-1.5 border border-gray-200 hover:bg-gray-100 text-sm rounded-lg text-gray-700 transition-colors">
              Download
            </button>
          </div>
        ))}
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-800">
        <p className="font-semibold mb-1">⚠ Human Approval Required</p>
        <p>Review all suggestions before implementation. Have a developer review each code snippet before applying.</p>
      </div>
    </div>
  );
}

// ── Main ReportViewer ──────────────────────────────────────────────────────────

export default function ReportViewer({ results, reportFiles, onDownload, token, auditId, apiBase }) {
  const [tab, setTab] = useState("ai");

  const pages     = results?.pages_data || [];
  const techData  = results?.technical_seo;
  const pagespeed = results?.suggestions?.pagespeed;
  const aiRec     = results?.suggestions?.ai_recommendations;

  const criticalCount = (pages.reduce((s, p) => s + (p.issues?.filter(i => i.priority === "critical").length || 0), 0))
    + (techData?.summary?.critical || 0);

  const tabs = [
    { key: "ai",         label: "🤖 AI Advisor" },
    { key: "overview",   label: "📊 Overview" },
    { key: "technical",  label: "⚙️ Technical" },
    { key: "pages",      label: `📄 All Pages (${pages.length})` },
    { key: "schema",     label: "🔧 Schema" },
    { key: "pagespeed",  label: "🚀 PageSpeed" },
    { key: "download",   label: "⬇️ Download" },
  ];

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h3 className="text-xl font-bold text-gray-900">Audit Results</h3>
          <p className="text-sm text-gray-500 mt-0.5">{results?.url}</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-lg text-xs font-semibold uppercase">
            {results?.audit_type}
          </span>
          {criticalCount > 0 && (
            <span className="px-2 py-1 bg-red-100 text-red-700 rounded-lg text-xs font-semibold">
              🔴 {criticalCount} Critical Issues
            </span>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-0.5 border-b border-gray-200 overflow-x-auto">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-3 py-2 text-sm font-medium whitespace-nowrap border-b-2 -mb-px transition-colors ${
              tab === t.key ? "border-blue-500 text-blue-600" : "border-transparent text-gray-500 hover:text-gray-700"
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div>
        {tab === "ai"        && <AIAdvisorTab aiRec={aiRec} />}
        {tab === "overview"  && <OverviewTab techData={techData} pages={pages} />}
        {tab === "technical" && <TechnicalTab data={techData} />}
        {tab === "pages"     && <AllPagesTab pages={pages} />}
        {tab === "schema"    && <SchemaTab pages={pages} />}
        {tab === "pagespeed" && <PageSpeedTab pagespeed={pagespeed} />}
        {tab === "download"  && <DownloadTab reportFiles={reportFiles} onDownload={onDownload} token={token} apiBase={apiBase} />}
      </div>
    </div>
  );
}
