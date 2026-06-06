import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch(path, token, options = {}) {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json", ...options.headers },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "API error");
  return data;
}

// ── Shared ────────────────────────────────────────────────────────────────────

const PAGE_TYPES = ["blog", "product", "category", "homepage", "landing", "service"];
const SCHEMA_TYPES = ["Article", "Product", "LocalBusiness", "FAQ", "BreadcrumbList", "Organization", "BlogPosting", "Review"];

// ── Content Brief ─────────────────────────────────────────────────────────────

function ContentBriefTab({ token }) {
  const [keyword, setKeyword]   = useState("");
  const [url, setUrl]           = useState("");
  const [pageType, setPageType] = useState("blog");
  const [crawl, setCrawl]       = useState(false);
  const [loading, setLoading]   = useState(false);
  const [brief, setBrief]       = useState(null);
  const [error, setError]       = useState("");
  const [copied, setCopied]     = useState(false);

  const generate = async () => {
    if (!keyword.trim()) { setError("Enter a target keyword"); return; }
    setLoading(true); setError(""); setBrief(null);
    try {
      const data = await apiFetch("/api/tools/content-brief", token, {
        method: "POST",
        body: JSON.stringify({ keyword: keyword.trim(), page_type: pageType, url: url.trim(), crawl_url: crawl }),
      });
      setBrief(data);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const copyBrief = () => {
    if (!brief) return;
    const text = `# Content Brief: ${brief.meta_title || keyword}

**Search Intent:** ${brief.search_intent || ""}
**H1:** ${brief.h1 || ""}
**Meta Title:** ${brief.meta_title || ""}
**Meta Description:** ${brief.meta_description || ""}
**Target Word Count:** ${brief.target_word_count || 1500}
**Content Angle:** ${brief.content_angle || ""}

## Outline
${(brief.outline || []).map((s, i) => `\n### ${i + 1}. ${s.h2}\n${(s.h3s || []).map(h => `  - ${h}`).join("\n")}\n**Key points:** ${(s.key_points || []).join(", ")}`).join("\n")}

## Semantic Keywords
${(brief.semantic_keywords || []).join(" · ")}

## Questions to Answer
${(brief.questions_to_answer || []).map(q => `- ${q}`).join("\n")}

## FAQ
${(brief.faq || []).map(f => `**Q:** ${f.q}\n**A:** ${f.a}`).join("\n\n")}

## CTA
${brief.cta || ""}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-4">
      <div className="card space-y-4">
        <p className="text-sm font-semibold" style={{ color:"#e2e8f0" }}>📝 Content Brief Generator</p>
        <p className="text-xs" style={{ color:"#4b5563" }}>
          Target keyword dalo — AI ek complete SEO brief banayega: outline, headings, FAQs, semantic keywords, sab kuch.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold mb-1" style={{ color:"#00d4ff" }}>Target Keyword *</label>
            <input className="input-field" value={keyword} onChange={e => setKeyword(e.target.value)}
              placeholder="e.g. sell old phone online" onKeyDown={e => e.key === "Enter" && generate()} />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1" style={{ color:"#6b7280" }}>Page Type</label>
            <select className="input-field" value={pageType} onChange={e => setPageType(e.target.value)}>
              {PAGE_TYPES.map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
            </select>
          </div>
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1" style={{ color:"#6b7280" }}>URL (optional — crawl for extra context)</label>
          <div className="flex gap-2">
            <input className="input-field flex-1" value={url} onChange={e => setUrl(e.target.value)}
              placeholder="https://bechdu.in/sell-old-phone" />
            <label className="flex items-center gap-2 text-xs cursor-pointer whitespace-nowrap px-3 rounded-lg"
              style={{ background:"rgba(255,255,255,0.04)", border:"1px solid rgba(255,255,255,0.08)", color:"#6b7280" }}>
              <input type="checkbox" checked={crawl} onChange={e => setCrawl(e.target.checked)} />
              Crawl page
            </label>
          </div>
        </div>
        {error && <p className="text-xs" style={{ color:"#ef4444" }}>⚠ {error}</p>}
        <button onClick={generate} disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
          {loading ? (
            <><div className="animate-spin w-4 h-4 rounded-full" style={{ border:"2px solid rgba(255,255,255,0.3)", borderTopColor:"white" }}/> Generating Brief...</>
          ) : "📝 Generate Content Brief"}
        </button>
      </div>

      {brief && (
        <div className="space-y-4">
          {/* Header */}
          <div className="card space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-widest" style={{ color:"#4b5563" }}>Brief Ready</p>
              <button onClick={copyBrief}
                className="text-xs px-3 py-1.5 rounded-lg font-medium"
                style={{ background:"rgba(0,212,255,0.1)", color:"#00d4ff", border:"1px solid rgba(0,212,255,0.25)" }}>
                {copied ? "✓ Copied!" : "📋 Copy Brief"}
              </button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {[
                { label: "Search Intent", val: brief.search_intent, color: "#a78bfa" },
                { label: "Target Words", val: brief.target_word_count, color: "#22c55e" },
                { label: "Ranking Time", val: brief.estimated_ranking_time, color: "#fbbf24" },
              ].map(c => (
                <div key={c.label} className="rounded-lg p-3 text-center"
                  style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.07)" }}>
                  <p className="text-xs uppercase tracking-widest" style={{ color:"#4b5563" }}>{c.label}</p>
                  <p className="text-sm font-bold mt-1 capitalize" style={{ color: c.color }}>{c.val || "—"}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Meta */}
          <div className="card space-y-3">
            <p className="text-xs font-semibold uppercase tracking-widest" style={{ color:"#4b5563" }}>Meta Tags</p>
            {[
              { label: "H1", val: brief.h1 },
              { label: "Meta Title", val: brief.meta_title },
              { label: "Meta Description", val: brief.meta_description },
              { label: "Content Angle", val: brief.content_angle },
            ].map(f => f.val ? (
              <div key={f.label}>
                <p className="text-xs font-semibold mb-1" style={{ color:"#6b7280" }}>{f.label}</p>
                <p className="text-sm px-3 py-2 rounded-lg" style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.07)", color:"#e2e8f0" }}>
                  {f.val}
                </p>
              </div>
            ) : null)}
          </div>

          {/* Outline */}
          {brief.outline?.length > 0 && (
            <div className="card space-y-3">
              <p className="text-xs font-semibold uppercase tracking-widest" style={{ color:"#4b5563" }}>Content Outline</p>
              {brief.outline.map((section, i) => (
                <div key={i} className="rounded-lg p-3 space-y-2"
                  style={{ background:"rgba(0,212,255,0.04)", border:"1px solid rgba(0,212,255,0.12)" }}>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-black w-5 h-5 rounded flex items-center justify-center flex-shrink-0"
                      style={{ background:"rgba(0,212,255,0.2)", color:"#00d4ff" }}>{i + 1}</span>
                    <p className="text-sm font-semibold" style={{ color:"#e2e8f0" }}>{section.h2}</p>
                    {section.word_target && <span className="text-xs ml-auto" style={{ color:"#374151" }}>~{section.word_target}w</span>}
                  </div>
                  {section.h3s?.length > 0 && (
                    <div className="ml-7 space-y-1">
                      {section.h3s.map((h, j) => (
                        <p key={j} className="text-xs" style={{ color:"#6b7280" }}>→ {h}</p>
                      ))}
                    </div>
                  )}
                  {section.key_points?.length > 0 && (
                    <p className="text-xs ml-7" style={{ color:"#374151" }}>
                      Cover: {section.key_points.join(" · ")}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Keywords + Questions */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {brief.semantic_keywords?.length > 0 && (
              <div className="card space-y-2">
                <p className="text-xs font-semibold uppercase tracking-widest" style={{ color:"#4b5563" }}>Semantic Keywords</p>
                <div className="flex flex-wrap gap-2">
                  {brief.semantic_keywords.map((kw, i) => (
                    <span key={i} className="text-xs px-2.5 py-1 rounded-full"
                      style={{ background:"rgba(167,139,250,0.1)", color:"#a78bfa", border:"1px solid rgba(167,139,250,0.2)" }}>
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {brief.questions_to_answer?.length > 0 && (
              <div className="card space-y-2">
                <p className="text-xs font-semibold uppercase tracking-widest" style={{ color:"#4b5563" }}>Questions to Answer</p>
                {brief.questions_to_answer.map((q, i) => (
                  <p key={i} className="text-xs" style={{ color:"#94a3b8" }}>❓ {q}</p>
                ))}
              </div>
            )}
          </div>

          {/* FAQ */}
          {brief.faq?.length > 0 && (
            <div className="card space-y-3">
              <p className="text-xs font-semibold uppercase tracking-widest" style={{ color:"#4b5563" }}>FAQ Section</p>
              {brief.faq.map((f, i) => (
                <div key={i} className="rounded-lg p-3"
                  style={{ background:"rgba(255,255,255,0.02)", border:"1px solid rgba(255,255,255,0.06)" }}>
                  <p className="text-xs font-semibold" style={{ color:"#fbbf24" }}>Q: {f.q}</p>
                  <p className="text-xs mt-1" style={{ color:"#6b7280" }}>A: {f.a}</p>
                </div>
              ))}
            </div>
          )}

          {/* CTA */}
          {brief.cta && (
            <div className="card">
              <p className="text-xs font-semibold mb-1" style={{ color:"#4b5563" }}>Recommended CTA</p>
              <p className="text-sm" style={{ color:"#22c55e" }}>→ {brief.cta}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Schema Generator ──────────────────────────────────────────────────────────

function SchemaTab({ token }) {
  const [url, setUrl]               = useState("");
  const [schemaType, setSchemaType] = useState("Article");
  const [loading, setLoading]       = useState(false);
  const [result, setResult]         = useState(null);
  const [error, setError]           = useState("");
  const [copied, setCopied]         = useState(false);

  const generate = async () => {
    if (!url.trim()) { setError("Enter a page URL"); return; }
    if (!url.startsWith("http")) { setError("URL must start with http:// or https://"); return; }
    setLoading(true); setError(""); setResult(null);
    try {
      const data = await apiFetch("/api/tools/schema", token, {
        method: "POST",
        body: JSON.stringify({ url: url.trim(), schema_type: schemaType }),
      });
      setResult(data);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const schemaStr = result?.json_ld ? JSON.stringify(result.json_ld, null, 2) : "";
  const scriptTag = schemaStr ? `<script type="application/ld+json">\n${schemaStr}\n</script>` : "";

  const copy = () => {
    navigator.clipboard.writeText(scriptTag);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-4">
      <div className="card space-y-4">
        <p className="text-sm font-semibold" style={{ color:"#e2e8f0" }}>🔧 Schema Markup Generator</p>
        <p className="text-xs" style={{ color:"#4b5563" }}>
          Page URL dalo + schema type choose karo — AI valid JSON-LD banayega jo Google Rich Results mein kaam aayega.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold mb-1" style={{ color:"#00d4ff" }}>Page URL *</label>
            <input className="input-field" value={url} onChange={e => setUrl(e.target.value)}
              placeholder="https://bechdu.in/sell-phone" />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1" style={{ color:"#6b7280" }}>Schema Type</label>
            <select className="input-field" value={schemaType} onChange={e => setSchemaType(e.target.value)}>
              {SCHEMA_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
        </div>
        {error && <p className="text-xs" style={{ color:"#ef4444" }}>⚠ {error}</p>}
        <button onClick={generate} disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
          {loading ? (
            <><div className="animate-spin w-4 h-4 rounded-full" style={{ border:"2px solid rgba(255,255,255,0.3)", borderTopColor:"white" }}/> Crawling page & generating schema...</>
          ) : "🔧 Generate Schema Markup"}
        </button>
      </div>

      {result && (
        <div className="card space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-widest" style={{ color:"#4b5563" }}>
              {result.schema_type} Schema — ready to paste in &lt;head&gt;
            </p>
            <button onClick={copy}
              className="text-xs px-3 py-1.5 rounded-lg font-medium"
              style={{ background:"rgba(0,212,255,0.1)", color:"#00d4ff", border:"1px solid rgba(0,212,255,0.25)" }}>
              {copied ? "✓ Copied!" : "📋 Copy <script> tag"}
            </button>
          </div>
          <pre className="text-xs p-4 rounded-xl overflow-x-auto"
            style={{ background:"rgba(0,0,0,0.4)", border:"1px solid rgba(255,255,255,0.08)", color:"#22c55e", fontFamily:"monospace", maxHeight:"400px" }}>
            {scriptTag}
          </pre>
          <div className="rounded-lg p-3 text-xs space-y-1"
            style={{ background:"rgba(251,191,36,0.06)", border:"1px solid rgba(251,191,36,0.15)", color:"#6b7280" }}>
            <p className="font-semibold" style={{ color:"#fbbf24" }}>⚠ Before using:</p>
            <p>• Placeholder values jaise <code>[Your Brand Name]</code> replace karo apni actual info se</p>
            <p>• Google Rich Results Test pe verify karo: search.google.com/test/rich-results</p>
            <p>• Site ke &lt;head&gt; section mein paste karo</p>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Domain Authority ──────────────────────────────────────────────────────────

function DomainAuthorityTab({ token }) {
  const [domainsInput, setDomainsInput] = useState("bechdu.in, cashify.in");
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState(null);
  const [error, setError]     = useState("");

  const check = async () => {
    if (!domainsInput.trim()) { setError("Enter at least one domain"); return; }
    setLoading(true); setError(""); setResult(null);
    try {
      const data = await apiFetch(`/api/tools/domain-authority?domains=${encodeURIComponent(domainsInput.trim())}`, token);
      setResult(data);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const PR_COLOR = (val) => {
    if (val == null) return "#374151";
    if (val >= 7) return "#22c55e";
    if (val >= 4) return "#fbbf24";
    return "#ef4444";
  };

  return (
    <div className="space-y-4">
      <div className="card space-y-4">
        <p className="text-sm font-semibold" style={{ color:"#e2e8f0" }}>🌐 Domain Authority Checker</p>
        <p className="text-xs" style={{ color:"#4b5563" }}>
          OpenPageRank API use karta hai — completely free (100 req/day). Ek domain ya comma-separated multiple domains daalo.
        </p>
        <div>
          <label className="block text-xs font-semibold mb-1" style={{ color:"#00d4ff" }}>Domains (comma-separated)</label>
          <input className="input-field" value={domainsInput} onChange={e => setDomainsInput(e.target.value)}
            placeholder="bechdu.in, cashify.in, olx.in" />
        </div>
        {error && <p className="text-xs" style={{ color:"#ef4444" }}>⚠ {error}</p>}
        <button onClick={check} disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
          {loading ? (
            <><div className="animate-spin w-4 h-4 rounded-full" style={{ border:"2px solid rgba(255,255,255,0.3)", borderTopColor:"white" }}/> Checking...</>
          ) : "🌐 Check Domain Authority"}
        </button>
      </div>

      {result && (
        <div className="card space-y-4">
          {result.no_key ? (
            <div className="rounded-xl p-4 space-y-2"
              style={{ background:"rgba(251,191,36,0.06)", border:"1px solid rgba(251,191,36,0.2)" }}>
              <p className="text-sm font-semibold" style={{ color:"#fbbf24" }}>🔑 API Key Required</p>
              <p className="text-xs" style={{ color:"#6b7280" }}>{result.message}</p>
              <div className="text-xs space-y-1 mt-2" style={{ color:"#4b5563" }}>
                <p>1. openpagerank.com pe free account banao</p>
                <p>2. API key copy karo</p>
                <p>3. <code className="px-1 rounded" style={{ background:"rgba(255,255,255,0.08)" }}>backend/.env</code> mein add karo: <code>OPR_API_KEY=your-key</code></p>
                <p>4. Backend restart karo</p>
              </div>
            </div>
          ) : (
            <>
              <p className="text-xs font-semibold uppercase tracking-widest" style={{ color:"#4b5563" }}>
                Domain Authority Scores (OpenPageRank 0-10)
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {result.domains?.map((d, i) => (
                  <div key={i} className="rounded-xl p-4 text-center space-y-2"
                    style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.07)" }}>
                    <p className="text-xs font-mono font-semibold" style={{ color:"#94a3b8" }}>{d.domain}</p>
                    <p className="text-4xl font-black" style={{ color: PR_COLOR(d.page_rank_integer) }}>
                      {d.page_rank_integer ?? "—"}
                    </p>
                    <p className="text-xs" style={{ color:"#374151" }}>out of 10</p>
                    {d.rank && <p className="text-xs" style={{ color:"#374151" }}>Global rank: #{parseInt(d.rank).toLocaleString()}</p>}
                    <div className="w-full rounded-full h-1.5 overflow-hidden" style={{ background:"rgba(255,255,255,0.06)" }}>
                      <div className="h-1.5 rounded-full transition-all"
                        style={{ width:`${(d.page_rank_integer || 0) * 10}%`, background: PR_COLOR(d.page_rank_integer) }}/>
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-xs" style={{ color:"#374151" }}>
                Score 0-10 scale — 7+ strong, 4-6 moderate, 0-3 weak. Based on OpenPageRank algorithm.
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
}

// ── Rank Tracker ──────────────────────────────────────────────────────────────

function RankTrackerTab({ token }) {
  const [keywords, setKeywords]     = useState([]);
  const [kwInput, setKwInput]       = useState("");
  const [siteInput, setSiteInput]   = useState("https://");
  const [loadingList, setLoadingList] = useState(false);
  const [addLoading, setAddLoading] = useState(false);
  const [histLoading, setHistLoading] = useState(false);
  const [selected, setSelected]     = useState(null);
  const [history, setHistory]       = useState(null);
  const [error, setError]           = useState("");
  const [loaded, setLoaded]         = useState(false);

  const loadKeywords = async () => {
    setLoadingList(true);
    try {
      const data = await apiFetch("/api/tools/rank-tracker", token);
      setKeywords(data);
      setLoaded(true);
    } catch (e) { setError(e.message); }
    finally { setLoadingList(false); }
  };

  const addKeyword = async () => {
    if (!kwInput.trim() || !siteInput.trim()) { setError("Enter keyword and site URL"); return; }
    setAddLoading(true); setError("");
    try {
      await apiFetch("/api/tools/rank-tracker", token, {
        method: "POST",
        body: JSON.stringify({ keyword: kwInput.trim(), site_url: siteInput.trim() }),
      });
      setKwInput("");
      await loadKeywords();
    } catch (e) { setError(e.message); }
    finally { setAddLoading(false); }
  };

  const removeKeyword = async (id) => {
    try {
      await apiFetch(`/api/tools/rank-tracker/${id}`, token, { method: "DELETE" });
      setKeywords(prev => prev.filter(k => k.id !== id));
      if (selected?.id === id) { setSelected(null); setHistory(null); }
    } catch (e) { setError(e.message); }
  };

  const loadHistory = async (kw) => {
    setSelected(kw); setHistLoading(true); setHistory(null); setError("");
    try {
      const enc_kw = encodeURIComponent(kw.keyword);
      const enc_site = encodeURIComponent(kw.site_url);
      const data = await apiFetch(`/api/tools/rank-tracker/history?keyword=${enc_kw}&site_url=${enc_site}&days=90`, token);
      setHistory(data);
    } catch (e) { setError(e.message); }
    finally { setHistLoading(false); }
  };

  if (!loaded) {
    return (
      <div className="card text-center py-12 space-y-4">
        <p className="text-4xl">📊</p>
        <div>
          <p className="text-lg font-bold" style={{ color:"#e2e8f0" }}>Keyword Rank Tracker</p>
          <p className="text-sm mt-2" style={{ color:"#4b5563" }}>
            Keywords add karo — GSC se daily position history dikhayega.<br/>
            GSC connected hona chahiye.
          </p>
        </div>
        <button onClick={loadKeywords} disabled={loadingList} className="btn-primary mx-auto flex items-center gap-2">
          {loadingList ? "Loading..." : "📊 Load Rank Tracker"}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Add keyword */}
      <div className="card space-y-3">
        <p className="text-sm font-semibold" style={{ color:"#e2e8f0" }}>📊 Keyword Rank Tracker</p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          <input className="input-field text-sm" value={kwInput} onChange={e => setKwInput(e.target.value)}
            placeholder="sell old phone" onKeyDown={e => e.key === "Enter" && addKeyword()} />
          <input className="input-field text-sm" value={siteInput} onChange={e => setSiteInput(e.target.value)}
            placeholder="https://bechdu.in" />
          <button onClick={addKeyword} disabled={addLoading} className="btn-primary text-sm">
            {addLoading ? "Adding..." : "+ Track Keyword"}
          </button>
        </div>
        {error && <p className="text-xs" style={{ color:"#ef4444" }}>⚠ {error}</p>}
        <p className="text-xs" style={{ color:"#374151" }}>
          Max 50 keywords · GSC connected rehna chahiye · Data 3-day lag ke saath
        </p>
      </div>

      {/* Keywords list */}
      {keywords.length === 0 ? (
        <div className="card text-center py-6">
          <p className="text-sm" style={{ color:"#4b5563" }}>No keywords tracked yet. Add your first keyword above.</p>
        </div>
      ) : (
        <div className="card space-y-2">
          <p className="text-xs font-semibold uppercase tracking-widest mb-2" style={{ color:"#4b5563" }}>
            Tracked Keywords ({keywords.length}/50)
          </p>
          {keywords.map(kw => (
            <div key={kw.id}
              className="flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all"
              style={{
                background: selected?.id === kw.id ? "rgba(0,212,255,0.08)" : "rgba(255,255,255,0.02)",
                border: `1px solid ${selected?.id === kw.id ? "rgba(0,212,255,0.3)" : "rgba(255,255,255,0.06)"}`,
              }}
              onClick={() => loadHistory(kw)}>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-mono font-semibold truncate" style={{ color:"#e2e8f0" }}>{kw.keyword}</p>
                <p className="text-xs truncate" style={{ color:"#374151" }}>{kw.site_url}</p>
              </div>
              <button onClick={e => { e.stopPropagation(); removeKeyword(kw.id); }}
                className="text-xs px-2 py-1 rounded"
                style={{ color:"#ef4444", background:"rgba(239,68,68,0.08)" }}>✕</button>
            </div>
          ))}
        </div>
      )}

      {/* History chart */}
      {selected && (
        <div className="card space-y-3">
          <p className="text-xs font-semibold uppercase tracking-widest" style={{ color:"#4b5563" }}>
            Position History — <span style={{ color:"#00d4ff" }}>{selected.keyword}</span>
          </p>
          {histLoading ? (
            <div className="flex justify-center py-6">
              <div className="animate-spin w-6 h-6 rounded-full" style={{ border:"2px solid rgba(0,212,255,0.2)", borderTopColor:"#00d4ff" }}/>
            </div>
          ) : history ? (
            <>
              <div className="grid grid-cols-3 gap-3 mb-2">
                {[
                  { label: "Current Position", val: history.current_position, color: "#00d4ff" },
                  { label: "Best (90d)",        val: history.best_position,    color: "#22c55e" },
                  { label: "Worst (90d)",       val: history.worst_position,   color: "#ef4444" },
                ].map(c => (
                  <div key={c.label} className="text-center rounded-lg p-3"
                    style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.07)" }}>
                    <p className="text-xs" style={{ color:"#4b5563" }}>{c.label}</p>
                    <p className="text-2xl font-black mt-1" style={{ color: c.color }}>
                      {c.val ? `#${c.val}` : "—"}
                    </p>
                  </div>
                ))}
              </div>

              {history.history.length === 0 ? (
                <p className="text-sm text-center py-4" style={{ color:"#4b5563" }}>
                  No GSC data for this keyword. Make sure this keyword drives impressions on your site.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr style={{ borderBottom:"1px solid rgba(255,255,255,0.06)" }}>
                        {["Date","Position","Clicks","Impressions","CTR"].map(h => (
                          <th key={h} className="text-left py-2 px-2 font-semibold uppercase tracking-wide" style={{ color:"#4b5563" }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {[...history.history].reverse().slice(0, 30).map((row, i) => (
                        <tr key={i} style={{ borderBottom:"1px solid rgba(255,255,255,0.03)" }}>
                          <td className="py-2 px-2" style={{ color:"#94a3b8" }}>{row.date}</td>
                          <td className="py-2 px-2 font-bold" style={{ color: row.position <= 10 ? "#22c55e" : row.position <= 20 ? "#fbbf24" : "#ef4444" }}>
                            #{row.position}
                          </td>
                          <td className="py-2 px-2" style={{ color:"#94a3b8" }}>{row.clicks}</td>
                          <td className="py-2 px-2" style={{ color:"#94a3b8" }}>{row.impressions.toLocaleString()}</td>
                          <td className="py-2 px-2" style={{ color:"#94a3b8" }}>{row.ctr}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          ) : null}
        </div>
      )}
    </div>
  );
}

// ── Main export ───────────────────────────────────────────────────────────────

export default function ToolsPanel({ token }) {
  const [tab, setTab] = useState("brief");

  const tabs = [
    { key: "brief",   label: "📝 Content Brief" },
    { key: "schema",  label: "🔧 Schema Generator" },
    { key: "da",      label: "🌐 Domain Authority" },
    { key: "tracker", label: "📊 Rank Tracker" },
  ];

  return (
    <div className="space-y-4">
      {/* Tab bar */}
      <div className="flex gap-1 flex-wrap">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className="text-sm px-4 py-2 rounded-lg font-medium transition-all"
            style={tab === t.key
              ? { background:"rgba(0,212,255,0.12)", color:"#00d4ff", border:"1px solid rgba(0,212,255,0.3)" }
              : { background:"rgba(255,255,255,0.03)", color:"#6b7280", border:"1px solid rgba(255,255,255,0.07)" }}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === "brief"   && <ContentBriefTab   token={token} />}
      {tab === "schema"  && <SchemaTab          token={token} />}
      {tab === "da"      && <DomainAuthorityTab token={token} />}
      {tab === "tracker" && <RankTrackerTab     token={token} />}
    </div>
  );
}
