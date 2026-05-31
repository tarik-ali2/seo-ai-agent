import { useState } from "react";
import { useRouter } from "next/router";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState("login"); // login | register
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  async function handleLogin(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const body = new URLSearchParams({ username: form.username, password: form.password });
      const res = await fetch(`${API}/api/auth/login`, { method: "POST", body });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Login failed");
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("username", data.username);
      router.push("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleRegister(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Registration failed");
      setMode("login");
      setError("");
      setForm({ username: form.username, email: "", password: "" });
      alert("Account created! Please login.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen grid-bg flex items-center justify-center p-4" style={{ background:"#030712" }}>
      {/* Ambient glows */}
      <div style={{ position:"fixed", top:"20%", left:"15%", width:400, height:400, background:"radial-gradient(circle, rgba(0,212,255,0.06) 0%, transparent 70%)", pointerEvents:"none" }}/>
      <div style={{ position:"fixed", bottom:"20%", right:"15%", width:300, height:300, background:"radial-gradient(circle, rgba(168,85,247,0.06) 0%, transparent 70%)", pointerEvents:"none" }}/>

      <div className="w-full max-w-md relative">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4"
            style={{ background:"linear-gradient(135deg,#004488,#0099cc)", boxShadow:"0 0 40px rgba(0,212,255,0.3), 0 0 80px rgba(0,212,255,0.1)" }}>
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h1 className="text-3xl font-black tracking-tight neon-cyan">SEO AI AGENT</h1>
          <p className="text-xs mt-2 font-mono" style={{ color:"#374151" }}>◈ Powered by Claude AI + Google PageSpeed ◈</p>
        </div>

        {/* Card */}
        <div className="card card-glow-cyan">
          <div style={{ position:"absolute", top:0, left:0, right:0, height:2, background:"linear-gradient(90deg, transparent, #00d4ff, #a855f7, #00d4ff, transparent)", borderRadius:"1rem 1rem 0 0" }}/>

          {/* Mode toggle */}
          <div className="flex p-1 mb-6 rounded-lg" style={{ background:"rgba(0,0,0,0.4)" }}>
            {["login", "register"].map((tab) => (
              <button key={tab} onClick={() => { setMode(tab); setError(""); }}
                className="flex-1 py-2 text-sm font-semibold rounded-md transition-all"
                style={mode === tab ? {
                  background:"rgba(0,212,255,0.15)", color:"#00d4ff",
                  boxShadow:"0 0 10px rgba(0,212,255,0.2)", border:"1px solid rgba(0,212,255,0.3)"
                } : { color:"#4b5563" }}>
                {tab === "login" ? "▶ Login" : "+ Register"}
              </button>
            ))}
          </div>

          <form onSubmit={mode === "login" ? handleLogin : handleRegister} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color:"#4b5563" }}>Username</label>
              <input name="username" type="text" value={form.username} onChange={handleChange}
                className="input-field font-mono" placeholder="enter_username" required />
            </div>
            {mode === "register" && (
              <div>
                <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color:"#4b5563" }}>Email</label>
                <input name="email" type="email" value={form.email} onChange={handleChange}
                  className="input-field" placeholder="you@example.com" required />
              </div>
            )}
            <div>
              <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color:"#4b5563" }}>Password</label>
              <input name="password" type="password" value={form.password} onChange={handleChange}
                className="input-field" placeholder="••••••••" required minLength={6} />
            </div>

            {error && (
              <div className="rounded-lg px-4 py-3 text-sm" style={{ background:"rgba(255,51,102,0.1)", border:"1px solid rgba(255,51,102,0.25)", color:"#ff3366" }}>
                ⚠ {error}
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full text-center">
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                  </svg>
                  {mode === "login" ? "Authenticating..." : "Creating account..."}
                </span>
              ) : mode === "login" ? "▶ Access System" : "+ Create Account"}
            </button>
          </form>

          {mode === "login" && (
            <div className="mt-4 p-3 rounded-lg text-xs font-mono" style={{ background:"rgba(0,212,255,0.05)", border:"1px solid rgba(0,212,255,0.1)", color:"#374151" }}>
              // Register a new account to begin. No email verification required.
            </div>
          )}
        </div>

        <p className="text-center text-xs mt-4 font-mono" style={{ color:"#1f2937" }}>SEO AI Agent v2047 · Claude AI + PageSpeed</p>
      </div>
    </div>
  );
}
