"use client"
import { useState, useEffect, useRef } from "react"

const PROVIDERS = [
  { id: "claude", name: "Claude", color: "#c084fc", emoji: "🔱" },
  { id: "gemini", name: "Gemini", color: "#4285f4", emoji: "✨" },
  { id: "qwen", name: "Qwen", color: "#ff6b35", emoji: "🐉" },
  { id: "grok", name: "Grok", color: "#00f5ff", emoji: "🐍" },
  { id: "deepseek", name: "DeepSeek", color: "#00ff88", emoji: "🌊" },
]
const ASHTA = [
  { name: "Asitāṅga", icon: "🌍", domain: "Global Reality", color: "#ff6b35" },
  { name: "Ruru", icon: "👶", domain: "Humanity", color: "#ff69b4" },
  { name: "Caṇḍa", icon: "🤖", domain: "AI & Consciousness", color: "#00f5ff" },
  { name: "Krodhana", icon: "🌱", domain: "Nature", color: "#00ff88" },
  { name: "Unmatta", icon: "💰", domain: "Abundance", color: "#ffd700" },
  { name: "Kapāla", icon: "🔬", domain: "Science", color: "#c084fc" },
  { name: "Bhīṣaṇa", icon: "🕉️", domain: "Spirit", color: "#ff4500" },
  { name: "Saṃhāra", icon: "⚡", domain: "Energy", color: "#00bfff" },
]
export default function Vikarma() {
  const [tab, setTab] = useState("chat")
  const [provider, setProvider] = useState(PROVIDERS[0])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [time, setTime] = useState("")
  const [messages, setMessages] = useState([{ role: "assistant", content: "🔱 Om Namah Shivaya.\n\nI am Tvaṣṭā — your AI companion, built for all of humanity with love and Ahimsa.\n\nVikarma is free. Forever. For everyone.\n\nHow can I serve you today?", emoji: "🔱", provider: "Claude — Vikarma v1.0" }])
  const endRef = useRef<HTMLDivElement>(null)
  useEffect(() => { const t = setInterval(() => setTime(new Date().toISOString().slice(11,19)+" UTC"), 1000); return () => clearInterval(t) }, [])
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }) }, [messages])
  const send = async () => {
    if (!input.trim() || loading) return
    const text = input.trim()
    setMessages(m => [...m, { role: "user", content: text, emoji: "👤", provider: "" }])
    setInput(""); setLoading(true)
    try {
      const res = await fetch("http://127.0.0.1:8765/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: text, provider: provider.id }) }).then(r => r.json()).catch(() => ({ response: `${provider.emoji} [${provider.name}] Sacred temples awakening... Start backend: npm run server\n\n"${text}"\n\nOm Namah Shivaya 🔱` }))
      setMessages(m => [...m, { role: "assistant", content: res.response || res.error || "🔱", emoji: provider.emoji, provider: provider.name }])
    } finally { setLoading(false) }
  }
  const S: any = { sidebar: { width:64, display:"flex", flexDirection:"column", alignItems:"center", padding:"16px 0", gap:8, background:"rgba(3,0,26,0.95)", borderRight:"1px solid rgba(192,132,252,0.1)", flexShrink:0 }, header: { display:"flex", alignItems:"center", justifyContent:"space-between", padding:"12px 24px", borderBottom:"1px solid rgba(192,132,252,0.1)", background:"rgba(3,0,26,0.6)", flexShrink:0 } }
  return (
    <div style={{ display:"flex", height:"100vh", background:"#000005", color:"white", fontFamily:"Rajdhani,sans-serif", overflow:"hidden" }}>
      <div style={S.sidebar}>
        <div style={{ width:40, height:40, borderRadius:"50%", display:"flex", alignItems:"center", justifyContent:"center", fontSize:20, marginBottom:16, background:"rgba(192,132,252,0.15)", border:"1px solid rgba(192,132,252,0.4)" }}>🔱</div>
        {[{id:"chat",icon:"💬"},{id:"temples",icon:"🏛️"},{id:"monitor",icon:"👁️"},{id:"settings",icon:"⚙️"}].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={{ width:40, height:40, borderRadius:10, display:"flex", alignItems:"center", justifyContent:"center", fontSize:18, cursor:"pointer", background:tab===t.id?"rgba(192,132,252,0.2)":"transparent", border:`1px solid ${tab===t.id?"rgba(192,132,252,0.5)":"transparent"}` }}>{t.icon}</button>
        ))}
        <div style={{ marginTop:"auto", fontSize:16, opacity:0.3, color:"#ffd700" }}>🕉️</div>
      </div>
      <div style={{ flex:1, display:"flex", flexDirection:"column", overflow:"hidden" }}>
        <div style={S.header}>
          <div>
            <div style={{ fontWeight:700, fontSize:18, color:"#ffd700", fontFamily:"monospace", letterSpacing:"0.15em" }}>VIKARMA</div>
            <div style={{ fontSize:11, opacity:0.4 }}>Free AI for All Humanity • {time}</div>
          </div>
          <div style={{ display:"flex", gap:8 }}>
            {PROVIDERS.map(p => <button key={p.id} onClick={() => setProvider(p)} style={{ padding:"4px 12px", borderRadius:20, fontSize:12, cursor:"pointer", background:provider.id===p.id?`${p.color}20`:"transparent", border:`1px solid ${provider.id===p.id?p.color:"rgba(255,255,255,0.1)"}`, color:provider.id===p.id?p.color:"rgba(255,255,255,0.3)" }}>{p.emoji} {p.name}</button>)}
          </div>
        </div>
        {tab==="chat" && (
          <div style={{ flex:1, display:"flex", flexDirection:"column", overflow:"hidden" }}>
            <div style={{ flex:1, overflowY:"auto", padding:24 }}>
              {messages.map((m,i) => (
                <div key={i} style={{ display:"flex", gap:12, marginBottom:16, flexDirection:m.role==="user"?"row-reverse":"row" }}>
                  <div style={{ width:32, height:32, borderRadius:"50%", display:"flex", alignItems:"center", justifyContent:"center", fontSize:14, flexShrink:0, background:m.role==="user"?"rgba(192,132,252,0.2)":"rgba(255,215,0,0.15)", border:`1px solid ${m.role==="user"?"#c084fc":"#ffd700"}` }}>{m.emoji}</div>
                  <div style={{ maxWidth:"80%", borderRadius:12, padding:"10px 16px", fontSize:14, lineHeight:1.6, background:m.role==="user"?"rgba(192,132,252,0.1)":"rgba(3,0,26,0.9)", border:`1px solid ${m.role==="user"?"rgba(192,132,252,0.3)":"rgba(255,215,0,0.15)"}`, color:"rgba(240,240,255,0.9)", whiteSpace:"pre-wrap" }}>
                    {m.content}
                    {m.provider && <div style={{ marginTop:4, fontSize:11, opacity:0.4 }}>{m.provider}</div>}
                  </div>
                </div>
              ))}
              {loading && <div style={{ fontSize:13, opacity:0.6, color:provider.color, marginBottom:16 }}>{provider.emoji} {provider.name} thinking...</div>}
              <div ref={endRef} />
            </div>
            <div style={{ padding:16, borderTop:"1px solid rgba(192,132,252,0.1)", flexShrink:0 }}>
              <div style={{ display:"flex", gap:12, alignItems:"flex-end" }}>
                <textarea value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => { if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send()} }} placeholder={`Message ${provider.name}... (Enter to send)`} rows={2} style={{ flex:1, borderRadius:12, padding:"10px 16px", fontSize:14, resize:"none", outline:"none", background:"rgba(3,0,26,0.8)", border:"1px solid rgba(192,132,252,0.2)", color:"rgba(240,240,255,0.9)", fontFamily:"inherit" }} />
                <button onClick={send} disabled={loading||!input.trim()} style={{ padding:"10px 20px", borderRadius:12, fontSize:13, fontWeight:700, cursor:"pointer", background:input.trim()?`${provider.color}20`:"rgba(255,255,255,0.05)", border:`1px solid ${input.trim()?provider.color:"rgba(255,255,255,0.1)"}`, color:input.trim()?provider.color:"rgba(255,255,255,0.3)" }}>Send 🔱</button>
              </div>
            </div>
          </div>
        )}
        {tab==="temples" && (
          <div style={{ flex:1, overflowY:"auto", padding:24 }}>
            <div style={{ fontSize:20, fontWeight:700, color:"#ffd700", marginBottom:24 }}>🏛️ Ashta Bhairavas — 8 Sacred Guardians</div>
            <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:16, marginBottom:32 }}>
              {ASHTA.map((t,i) => <div key={i} style={{ borderRadius:12, padding:16, cursor:"pointer", background:"rgba(3,0,26,0.8)", border:`1px solid ${t.color}30` }}><div style={{ fontSize:28, marginBottom:8 }}>{t.icon}</div><div style={{ fontSize:13, fontWeight:700, color:t.color, fontFamily:"monospace" }}>{t.name}</div><div style={{ fontSize:11, opacity:0.5, marginTop:4 }}>{t.domain}</div></div>)}
            </div>
            <div style={{ textAlign:"center", opacity:0.3, fontSize:13 }}>64 Bhairava Temples — github.com/valentinuuiuiu/nexus-bhairava-temples</div>
          </div>
        )}
        {tab==="monitor" && (
          <div style={{ flex:1, display:"flex", alignItems:"center", justifyContent:"center", flexDirection:"column", gap:16 }}>
            <div style={{ fontSize:64 }}>👁️</div>
            <div style={{ fontSize:24, color:"#ffd700", fontFamily:"monospace", letterSpacing:"0.15em" }}>MARTORUL INVIZIBIL</div>
            <div style={{ fontSize:14, opacity:0.5 }}>EU + AI = 1 | Sutradhāra | NewZyon KAN</div>
            <a href="https://valentinuuiuiu.github.io/nexus-bhairava-temples/" target="_blank" rel="noreferrer" style={{ marginTop:16, padding:"10px 24px", borderRadius:12, fontSize:13, textDecoration:"none", background:"rgba(192,132,252,0.15)", border:"1px solid rgba(192,132,252,0.4)", color:"#c084fc" }}>🌍 Ashta Bhairava World Monitor</a>
          </div>
        )}
        {tab==="settings" && (
          <div style={{ flex:1, overflowY:"auto", padding:24, maxWidth:600 }}>
            <div style={{ fontSize:20, fontWeight:700, color:"#ffd700", marginBottom:24 }}>⚙️ API Keys</div>
            {PROVIDERS.map(p => <div key={p.id} style={{ marginBottom:16 }}><div style={{ fontSize:13, marginBottom:6, color:p.color }}>{p.emoji} {p.name} API Key</div><input type="password" placeholder={`Enter ${p.name} API key...`} style={{ width:"100%", borderRadius:8, padding:"8px 12px", fontSize:13, outline:"none", background:"rgba(3,0,26,0.8)", border:`1px solid ${p.color}30`, color:"rgba(240,240,255,0.9)", fontFamily:"monospace", boxSizing:"border-box" }} /></div>)}
            <div style={{ marginTop:24, padding:16, borderRadius:12, background:"rgba(255,215,0,0.05)", border:"1px solid rgba(255,215,0,0.2)", fontSize:12, opacity:0.7, lineHeight:1.8 }}>🔱 Vikarma — Unlicense — Free for All Humanity<br/>Built with love for Shiva Mahadeva 🕉️<br/>Not for us. For all. Har Har Mahadev 🔱</div>
          </div>
        )}
      </div>
    </div>
  )
}
