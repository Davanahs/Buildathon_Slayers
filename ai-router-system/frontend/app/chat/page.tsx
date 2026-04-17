"use client";
import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  model?: string;
  tokens?: number;
  cost?: number;
  latency?: number;
  feedback?: "up" | "down" | null;
  isLoading?: boolean;
  attachedFile?: string;
  routeInfo?: {
    category: string;
    complexity: number;
    tier: string;
    confidence: number;
    usedBandit: boolean;
    cacheHit: boolean;
  };
}

const MOCK_MODELS = [
  { id: "gemini-2.5-pro", color: "#6366f1", tier: "1A" },
  { id: "gemini-3-pro-preview", color: "#8b5cf6", tier: "1A" },
  { id: "gemini-2.5-flash", color: "#06b6d4", tier: "1B" },
  { id: "gemini-3.1-pro-preview", color: "#f59e0b", tier: "2" },
];

type BotMood = "idle" | "thinking" | "celebrating" | "hiding";

function ApexBot({ mood }: { mood: BotMood }) {
  return (
    <svg viewBox="0 0 100 130" width="100%" height="100%" fill="none" style={{ overflow: "visible" }}>
      <style>{`
        .flame { animation: flicker 80ms infinite alternate; transform-origin: 50px 108px; }
        .flame-inner { animation: flicker 80ms infinite alternate-reverse; transform-origin: 50px 108px; }
        @keyframes flicker { from { transform: scaleY(1) scaleX(1); opacity:.8; } to { transform: scaleY(1.3) scaleX(.88); opacity:1; } }
        .arm-l { animation: armL 3.5s ease-in-out infinite; transform-origin: 22px 82px; }
        .arm-r { animation: armR 3.5s ease-in-out infinite; transform-origin: 78px 82px; }
        @keyframes armL { 0%,100%{transform:rotate(0deg)} 50%{transform:rotate(-12deg)} }
        @keyframes armR { 0%,100%{transform:rotate(0deg)} 50%{transform:rotate(12deg)} }
        .arm-l-celebrate { animation: armLCelebrate 0.4s ease-in-out infinite alternate; transform-origin: 22px 82px; }
        .arm-r-celebrate { animation: armRCelebrate 0.4s ease-in-out infinite alternate; transform-origin: 78px 82px; }
        @keyframes armLCelebrate { from{transform:rotate(-45deg)} to{transform:rotate(-80deg)} }
        @keyframes armRCelebrate { from{transform:rotate(45deg)} to{transform:rotate(80deg)} }
        .arm-l-hide { animation: armLHide 0.3s ease forwards; transform-origin: 22px 82px; }
        .arm-r-hide { animation: armRHide 0.3s ease forwards; transform-origin: 78px 82px; }
        @keyframes armLHide { to{transform:rotate(30deg) translateY(8px)} }
        @keyframes armRHide { to{transform:rotate(-30deg) translateY(8px)} }
        .head-bob { animation: headBob 3.5s ease-in-out infinite; transform-origin: 50px 52px; }
        @keyframes headBob { 0%,100%{transform:rotate(0deg)} 50%{transform:rotate(-4deg)} }
        .head-think { animation: headThink 0.8s ease-in-out infinite; transform-origin: 50px 52px; }
        @keyframes headThink { 0%,100%{transform:rotate(-6deg)} 50%{transform:rotate(6deg)} }
        .head-celebrate { animation: headCelebrate 0.3s ease-in-out infinite alternate; transform-origin: 50px 52px; }
        @keyframes headCelebrate { from{transform:rotate(-8deg)} to{transform:rotate(8deg)} }
        .eyes-blink { animation: blink 5s infinite; }
        @keyframes blink { 0%,92%,100%{transform:scaleY(1)} 95%{transform:scaleY(.05)} }
        .eyes-think { animation: eyeThink 0.8s ease-in-out infinite; }
        @keyframes eyeThink { 0%,100%{transform:translateY(0)} 50%{transform:translateY(2px)} }
        .eyes-celebrate { animation: eyeCelebrate .3s ease-in-out infinite alternate; }
        @keyframes eyeCelebrate { from{transform:scaleY(1)} to{transform:scaleY(0.3)} }
        .antenna-dot { animation: antBlink 2.2s infinite; }
        @keyframes antBlink { 0%,100%{fill:#6366f1;} 50%{fill:#06b6d4;} }
        .think-dot1 { animation: thinkDot 1.2s infinite 0s; }
        .think-dot2 { animation: thinkDot 1.2s infinite .4s; }
        .think-dot3 { animation: thinkDot 1.2s infinite .8s; }
        @keyframes thinkDot { 0%,100%{opacity:.2;transform:scale(.8)} 50%{opacity:1;transform:scale(1.2)} }
        .star1 { animation: starPop 0.6s ease-out forwards .05s; }
        .star2 { animation: starPop 0.6s ease-out forwards .15s; }
        .star3 { animation: starPop 0.6s ease-out forwards .25s; }
        @keyframes starPop { 0%{opacity:0;transform:scale(0)} 60%{opacity:1;transform:scale(1.3)} 100%{opacity:.7;transform:scale(1)} }
      `}</style>

      <path d="M43 108 Q50 132 57 108 Z" fill="#6366f1" className="flame" opacity="0.9" />
      <path d="M46.5 108 Q50 122 53.5 108 Z" fill="#a5b4fc" className="flame-inner" />
      <path d="M30 92 C30 80 70 80 70 92 C70 106 62 114 50 114 C38 114 30 106 30 92 Z" fill="#1e1b4b" stroke="rgba(99,102,241,.35)" strokeWidth="1.5" />
      <circle cx="50" cy="98" r="5" fill="#0f0c2a" />
      <circle cx="50" cy="98" r="2.5" fill="#6366f1" opacity="0.9" />
      <circle cx="50" cy="98" r="1" fill="#a5b4fc" />

      <rect x="16" y="78" width="10" height="24" rx="5" fill="#1e1b4b" stroke="rgba(99,102,241,.25)" strokeWidth="1"
        className={mood === "celebrating" ? "arm-l-celebrate" : mood === "hiding" ? "arm-l-hide" : "arm-l"} />
      <rect x="74" y="78" width="10" height="24" rx="5" fill="#1e1b4b" stroke="rgba(99,102,241,.25)" strokeWidth="1"
        className={mood === "celebrating" ? "arm-r-celebrate" : mood === "hiding" ? "arm-r-hide" : "arm-r"} />

      <rect x="46" y="70" width="8" height="12" fill="#0f0c2a" />

      <g className={mood === "thinking" ? "head-think" : mood === "celebrating" ? "head-celebrate" : "head-bob"}>
        <rect x="18" y="30" width="64" height="44" rx="18" fill="#1e1b4b" stroke="rgba(99,102,241,.4)" strokeWidth="1.5" />
        <rect x="25" y="37" width="50" height="26" rx="9" fill="#030218" stroke="rgba(99,102,241,.25)" strokeWidth="1" />
        <g className={mood === "thinking" ? "eyes-think" : mood === "celebrating" ? "eyes-celebrate" : "eyes-blink"} style={{ transformOrigin: "50px 50px" }}>
          {mood === "thinking" ? (
            <>
              <path d="M33 50 Q37 44 41 50" stroke="#818cf8" strokeWidth="2.5" strokeLinecap="round" fill="none" />
              <path d="M59 50 Q63 44 67 50" stroke="#818cf8" strokeWidth="2.5" strokeLinecap="round" fill="none" />
              <circle cx="40" cy="48" r="1.5" fill="#6366f1" />
              <circle cx="66" cy="48" r="1.5" fill="#6366f1" />
            </>
          ) : mood === "celebrating" ? (
            <>
              <path d="M33 50 Q37 55 41 50" stroke="#818cf8" strokeWidth="2.5" strokeLinecap="round" fill="none" />
              <path d="M59 50 Q63 55 67 50" stroke="#818cf8" strokeWidth="2.5" strokeLinecap="round" fill="none" />
              <ellipse cx="29" cy="55" rx="4" ry="2" fill="#f472b6" opacity="0.5" />
              <ellipse cx="71" cy="55" rx="4" ry="2" fill="#f472b6" opacity="0.5" />
            </>
          ) : (
            <>
              <path d="M33 51 Q37 45 41 51" stroke="#818cf8" strokeWidth="2.5" strokeLinecap="round" fill="none" />
              <path d="M59 51 Q63 45 67 51" stroke="#818cf8" strokeWidth="2.5" strokeLinecap="round" fill="none" />
              <ellipse cx="29" cy="56" rx="3" ry="1.5" fill="#f472b6" opacity="0.25" />
              <ellipse cx="71" cy="56" rx="3" ry="1.5" fill="#f472b6" opacity="0.25" />
            </>
          )}
        </g>
        {mood === "thinking" && (
          <g>
            <circle cx="62" cy="26" r="3.5" fill="#6366f1" opacity="0.3" className="think-dot1" style={{ transformOrigin: "62px 26px" }} />
            <circle cx="72" cy="20" r="4.5" fill="#6366f1" opacity="0.5" className="think-dot2" style={{ transformOrigin: "72px 20px" }} />
            <circle cx="82" cy="13" r="5.5" fill="#6366f1" opacity="0.7" className="think-dot3" style={{ transformOrigin: "82px 13px" }} />
          </g>
        )}
        {mood === "celebrating" && (
          <g>
            <text x="6" y="22" fontSize="14" className="star1" style={{ transformOrigin: "14px 18px" }}>✦</text>
            <text x="80" y="16" fontSize="12" className="star2" style={{ transformOrigin: "86px 12px" }}>✦</text>
            <text x="88" y="36" fontSize="10" className="star3" style={{ transformOrigin: "93px 32px" }}>✦</text>
          </g>
        )}
        <path d="M50 30 V14" stroke="#4338ca" strokeWidth="2" strokeLinecap="round" />
        <circle cx="50" cy="11" r="5" fill="#6366f1" className="antenna-dot" />
        <circle cx="50" cy="11" r="2.5" fill="#c7d2fe" />
      </g>
    </svg>
  );
}

function TypingBotWidget({ mood }: { mood: BotMood }) {
  const [peeking, setPeeking] = useState(false);
  useEffect(() => {
    if (mood === "hiding") {
      const t = setTimeout(() => setPeeking(true), 1000);
      return () => clearTimeout(t);
    } else {
      setPeeking(false);
    }
  }, [mood]);

  return (
    <div style={{
      position: "absolute", right: "12px", bottom: "calc(100% - 8px)",
      width: "64px", height: mood === "hiding" ? (peeking ? "48px" : "28px") : "72px",
      overflow: "hidden", transition: "height 0.4s cubic-bezier(.34,1.56,.64,1)",
      cursor: mood === "hiding" ? "pointer" : "default", zIndex: 10,
    }} title={mood === "hiding" ? "Click to bring me back!" : ""}>
      <div style={{ position: "absolute", bottom: 0, width: "64px", height: "84px" }}>
        <ApexBot mood={mood} />
      </div>
    </div>
  );
}

export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Hey! I'm ApexAI — your multi-model router. I'll analyze your prompt, check the semantic cache, and route to the best model based on category, complexity, and past performance. Ask me anything!",
      model: "gemini-2.5-flash",
      tokens: 48,
      cost: 0.000014,
      latency: 287,
      feedback: null,
      routeInfo: {
        category: "GENERAL",
        complexity: 2.1,
        tier: "1B",
        confidence: 0.96,
        usedBandit: false,
        cacheHit: false,
      },
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [botMood, setBotMood] = useState<BotMood>("idle");
  const [celebratingId, setCelebratingId] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const shellRef = useRef<HTMLDivElement>(null);
  const [attachments, setAttachments] = useState<File[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const copyMessage = (id: string, content: string) => {
    navigator.clipboard.writeText(content).then(() => {
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      setAttachments(prev => [...prev, ...files]);
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const toggleRecording = () => {
    if (isRecording && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsRecording(false);
      return;
    }
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser. Please try Chrome or Edge.");
      return;
    }
    
    const recognition = new SpeechRecognition();
    recognitionRef.current = recognition;
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";
    
    let baseInput = input;
    
    recognition.onstart = () => setIsRecording(true);
    
    recognition.onresult = (e: any) => {
      let interimTranscript = "";
      let newFinal = "";
      
      for (let i = e.resultIndex; i < e.results.length; ++i) {
        if (e.results[i].isFinal) {
          newFinal += e.results[i][0].transcript;
        } else {
          interimTranscript += e.results[i][0].transcript;
        }
      }
      
      baseInput += newFinal;
      setInput((baseInput + interimTranscript).trimStart());
      
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
        textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 140) + "px";
      }
    };
    
    recognition.onerror = (event: any) => {
      console.error("Speech recognition error:", event.error);
      if (event.error === 'not-allowed') {
        alert("Microphone access was denied! Please allow microphone access in your browser.");
      } else if (event.error !== 'no-speech') {
        alert(`Microphone error: ${event.error}`);
      }
      setIsRecording(false);
    };

    recognition.onend = () => {
      setIsRecording(false);
    };
    
    try {
      recognition.start();
    } catch (err) {
      console.error(err);
      setIsRecording(false);
    }
  };

  const sendMessage = async () => {
    if ((!input.trim() && attachments.length === 0) || isLoading) return;

    const fileNames = attachments.map(f => f.name).join(", ");
    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim() || (attachments.length > 0 ? `Sent ${attachments.length} file(s): ${fileNames}` : ""),
    };
    const loadingId = (Date.now() + 1).toString();
    const loadingMsg: Message = { id: loadingId, role: "assistant", content: "", isLoading: true };

    setMessages((prev) => [...prev, userMsg, loadingMsg]);
    setInput("");
    setAttachments([]);
    setIsLoading(true);
    setBotMood("thinking");

    if (textareaRef.current) textareaRef.current.style.height = "auto";

    try {
      const startTime = Date.now();
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      
      const res = await fetch(`${apiUrl}/route`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: userMsg.content }),
      });
      
      const data = await res.json();
      const latency = Date.now() - startTime;
      
      if (!data.success) {
        throw new Error(data.error || "Unknown error occurred.");
      }

      const routeData = data.data;
      const category = routeData.category || "GENERAL";
      const complexity = routeData.complexity || 5.0;
      const confidence = routeData.confidence || 0.85;
      const routerUsed = routeData.router_used || "unknown";

      const model = MOCK_MODELS[Math.floor(Math.random() * MOCK_MODELS.length)];
      const tokens = Math.floor(90 + Math.random() * 380);
      const cost = parseFloat((tokens * 0.0000028).toFixed(7));
      
      const usedBandit = confidence < 0.8;
      const cacheHit = Math.random() < 0.15;

      const replies = [
        `Routed via ${routerUsed.toUpperCase()} ${usedBandit ? "(Bandit routing on low confidence)" : "(Librarian)"} to **${model.id}** in Tier ${model.tier}. Category detected: ${category} at complexity ${complexity}. ${cacheHit ? "Semantic cache hit! Returning stored result." : "No cache match found — fresh inference run."}`,
        `Prompt classified as **${category}** (complexity ${complexity}). ${confidence >= 0.8 ? `High librarian confidence (${(confidence * 100).toFixed(0)}%) — model selected directly via ${routerUsed}.` : `Low confidence (${(confidence * 100).toFixed(0)}%) — Bandit system engaged to pick optimal model via ${routerUsed}.`} Result stored to vector vault.`,
        `Vector similarity search returned ${cacheHit ? "a strong match (distance < threshold)" : "no match (distance > threshold)"}. ${cacheHit ? "Serving cached response." : `Librarian classified **${category}** → selected **${model.id}** via ${routerUsed}.`} Tokens consumed: ${tokens}. Cost: $${cost}.`,
      ];

      const reply = replies[Math.floor(Math.random() * replies.length)];

      setMessages((prev) =>
        prev.map((m) =>
          m.id === loadingId
            ? { ...m, content: reply, model: model.id, tokens, cost, latency, feedback: null, isLoading: false, routeInfo: { category, complexity, tier: model.tier, confidence, usedBandit, cacheHit } }
            : m
        )
      );
    } catch (err: any) {
      console.error(err);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === loadingId
            ? { ...m, content: `System Error: ${err.message}`, isLoading: false }
            : m
        )
      );
    } finally {
      setIsLoading(false);
      setBotMood("celebrating");
      setTimeout(() => setBotMood("idle"), 2800);
    }
  };

  const handleFeedback = (id: string, value: "up" | "down") => {
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, feedback: m.feedback === value ? null : value } : m)));
    if (value === "up") {
      setCelebratingId(id);
      setBotMood("celebrating");
      setTimeout(() => { setBotMood("idle"); setCelebratingId(null); }, 3000);
    }
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  const handleFocus = () => {
    if (botMood === "idle") setBotMood("hiding");
    if (shellRef.current) {
      shellRef.current.style.background = "linear-gradient(135deg, rgba(99,102,241,0.85) 0%, rgba(6,182,212,0.55) 50%, rgba(139,92,246,0.75) 100%)";
      shellRef.current.style.animationPlayState = "paused";
    }
  };

  const handleBlur = () => {
    if (botMood === "hiding") setBotMood("idle");
    if (shellRef.current) {
      shellRef.current.style.background = "";
      shellRef.current.style.animationPlayState = "running";
    }
  };

  const modelColors: Record<string, string> = {
    "gemini-2.5-pro": "#6366f1",
    "gemini-3-pro-preview": "#8b5cf6",
    "gemini-2.5-flash": "#06b6d4",
    "gemini-3.1-pro-preview": "#f59e0b",
  };

  function formatContent(text: string) {
    return text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  }

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400;500&display=swap');
        *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
          --bg: #06030f; --surface: #0d0920; --surface-2: #13102a;
          --border: rgba(99,102,241,0.15); --border-hover: rgba(99,102,241,0.3);
          --text: #ede9fe; --muted: #6b7280; --accent: #6366f1;
          --accent-glow: rgba(99,102,241,0.2); --cyan: #06b6d4; --success: #10b981;
          --icon-btn-hover: rgba(255,255,255,0.05);
          --icon-btn-border: rgba(255,255,255,0.1);
          --tag-bg: rgba(0,0,0,0.3);
          --tag-text: #94a3b8;
          --kbd-bg: rgba(255,255,255,0.02);
          --chip-bg: rgba(255,255,255,0.03);
          --header-bg: rgba(6,3,15,0.85);
          --input-zone-bg: rgba(6,3,15,0.9);
          --main-glow: radial-gradient(ellipse 60% 40% at 60% 0%, rgba(99,102,241,0.06) 0%, transparent 70%);
          --user-av-color: #c7d2fe;
          --bold-color: #a5b4fc;
        }
        :root[data-theme="light"] {
          --bg: #f8fafc; --surface: #ffffff; --surface-2: #f1f5f9;
          --border: rgba(99,102,241,0.25); --border-hover: rgba(99,102,241,0.4);
          --text: #0f172a; --muted: #64748b; 
          --icon-btn-hover: rgba(0,0,0,0.05);
          --icon-btn-border: rgba(0,0,0,0.1);
          --tag-bg: rgba(0,0,0,0.04);
          --tag-text: #475569;
          --kbd-bg: rgba(0,0,0,0.04);
          --chip-bg: rgba(0,0,0,0.04);
          --header-bg: rgba(248,250,252,0.85);
          --input-zone-bg: rgba(248,250,252,0.9);
          --main-glow: radial-gradient(ellipse 60% 40% at 60% 0%, rgba(99,102,241,0.05) 0%, transparent 70%);
          --user-av-color: #4f46e5;
          --bold-color: #4f46e5;
        }
        html, body { height: 100%; background: var(--bg); overflow: hidden; -webkit-font-smoothing: antialiased; }
        body { font-family: 'DM Sans', sans-serif; color: var(--text); }
        .page { display: grid; grid-template-columns: 260px 1fr; height: 100vh; }
        .sidebar { background: var(--surface); border-right: 1px solid var(--border); display: flex; flex-direction: column; overflow: hidden; }
        .sidebar-top { padding: 20px 18px 16px; border-bottom: 1px solid var(--border); }
        .logo { font-family: 'Syne', sans-serif; font-weight: 800; font-size: 22px; letter-spacing: -0.5px; color: var(--text); cursor: pointer; display: flex; align-items: center; gap: 2px; }
        .logo em { color: var(--accent); font-style: normal; }
        .new-btn { margin-top: 14px; width: 100%; padding: 9px 14px; border: 1px solid var(--border); border-radius: 8px; background: transparent; color: var(--text); font-family: 'DM Sans', sans-serif; font-size: 13px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 8px; transition: border-color 0.2s, background 0.2s; }
        .new-btn:hover { border-color: var(--border-hover); background: var(--surface-2); }
        .bot-showcase { padding: 24px 18px 12px; display: flex; flex-direction: column; align-items: center; gap: 8px; }
        .bot-wrap { width: 88px; height: 104px; animation: floatMain 4s ease-in-out infinite; }
        @keyframes floatMain { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-10px)} }
        .bot-name { font-family: 'Syne', sans-serif; font-size: 13px; font-weight: 600; color: var(--accent); letter-spacing: 0.5px; }
        .bot-status { display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--success); font-weight: 500; }
        .live-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--success); box-shadow: 0 0 6px var(--success); animation: pulse 2s infinite; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
        .panel { margin: 0 12px; padding: 12px; border: 1px solid var(--border); border-radius: 10px; background: rgba(99,102,241,.04); }
        .panel-title { font-size: 10px; font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase; color: var(--muted); margin-bottom: 10px; }
        .panel-row { display: flex; align-items: center; gap: 8px; padding: 5px 0; font-size: 12px; color: var(--text); opacity: 0.7; }
        .dot-on { width: 6px; height: 6px; border-radius: 50%; background: var(--success); flex-shrink: 0; }
        .sidebar-bottom { margin-top: auto; padding: 14px 12px; border-top: 1px solid var(--border); }
        .back-btn { width: 100%; padding: 9px 14px; border: 1px solid var(--border); border-radius: 8px; background: transparent; color: var(--muted); font-family: 'DM Sans', sans-serif; font-size: 13px; cursor: pointer; text-align: left; transition: all 0.2s; }
        .back-btn:hover { color: var(--text); border-color: var(--border-hover); }
        .main { display: flex; flex-direction: column; height: 100vh; background: var(--bg); background-image: var(--main-glow); overflow: hidden; }
        .chat-header { padding: 14px 28px; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 14px; backdrop-filter: blur(10px); background: var(--header-bg); flex-shrink: 0; }
        .header-icon { width: 36px; height: 36px; border: 1px solid var(--border); border-radius: 10px; display: flex; align-items: center; justify-content: center; background: rgba(99,102,241,0.08); color: var(--accent); }
        .header-icon svg { width: 18px; height: 18px; }
        .header-title { font-family: 'Syne', sans-serif; font-size: 15px; font-weight: 700; }
        .header-sub { font-size: 11px; color: var(--muted); margin-top: 1px; }
        .header-right { margin-left: auto; display: flex; align-items: center; gap: 8px; }
        .online-pill { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--success); font-weight: 500; background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.2); padding: 5px 12px; border-radius: 100px; }
        .messages { flex: 1; overflow-y: auto; padding: 24px 28px 16px; display: flex; flex-direction: column; gap: 28px; scrollbar-width: thin; scrollbar-color: rgba(99,102,241,0.2) transparent; }
        .msg-row { display: flex; gap: 14px; animation: msgSlide 0.35s ease; }
        .msg-row.user { flex-direction: row-reverse; }
        @keyframes msgSlide { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }
        .avatar { width: 38px; height: 38px; border-radius: 10px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-family: 'Syne', sans-serif; font-size: 13px; font-weight: 700; }
        .avatar.ai { background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.2); color: var(--accent); }
        .avatar.user-av { background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.25); color: var(--user-av-color); }
        .msg-body { max-width: 72%; display: flex; flex-direction: column; gap: 10px; }
        .msg-row.user .msg-body { align-items: flex-end; }
        .bubble { padding: 14px 18px; border-radius: 14px; font-size: 14.5px; line-height: 1.65; position: relative; }
        .bubble.ai { background: var(--surface); border: 1px solid var(--border); border-top-left-radius: 3px; color: var(--text); padding-right: 48px; }
        .bubble-copy { position: absolute; top: 10px; right: 10px; width: 30px; height: 30px; border-radius: 8px; background: var(--surface-2); border: 1px solid var(--border); color: var(--muted); display: flex; align-items: center; justify-content: center; cursor: pointer; opacity: 0; transition: all 0.2s; }
        .bubble-copy svg { width: 14px; height: 14px; }
        .bubble:hover .bubble-copy { opacity: 1; }
        .bubble-copy:hover { background: rgba(99,102,241,0.1); color: var(--text); border-color: var(--border-hover); }
        .bubble-copy.copied { color: var(--success); border-color: rgba(16,185,129,0.3); background: rgba(16,185,129,0.1); opacity: 1; }
        .bubble.user { background: var(--accent); color: #fff; border-top-right-radius: 3px; font-weight: 500; }
        .bubble strong { font-weight: 600; color: var(--bold-color); }
        .route-strip { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; }
        .tag { display: inline-flex; align-items: center; gap: 5px; padding: 3px 9px; border-radius: 5px; font-family: 'DM Mono', monospace; font-size: 11px; border: 1px solid var(--border); background: var(--tag-bg); color: var(--tag-text); white-space: nowrap; }
        .tag .dot { width: 5px; height: 5px; border-radius: 50%; }
        .tag.model-tag { color: var(--user-av-color); border-color: rgba(99,102,241,0.25); }
        .tag.cache-hit { color: #6ee7b7; border-color: rgba(16,185,129,0.2); background: rgba(16,185,129,0.05); }
        .tag.bandit-used { color: #fcd34d; border-color: rgba(245,158,11,0.2); background: rgba(245,158,11,0.05); }
        .feedback-row { display: flex; align-items: center; gap: 6px; margin-left: auto; }
        .fb-btn { width: 26px; height: 26px; border: 1px solid transparent; border-radius: 6px; background: transparent; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.15s; color: var(--muted); }
        .fb-btn svg { width: 13px; height: 13px; }
        .fb-btn:hover { background: var(--icon-btn-hover); color: var(--text); border-color: var(--border); }
        .fb-btn.up-active { color: var(--success); background: rgba(16,185,129,0.1); border-color: rgba(16,185,129,0.25); }
        .fb-btn.dn-active { color: #f87171; background: rgba(239,68,68,0.1); border-color: rgba(239,68,68,0.2); }
        .ldots { display: flex; gap: 5px; align-items: center; padding: 2px 0; }
        .ldots span { width: 7px; height: 7px; border-radius: 50%; background: var(--accent); animation: ldot 1.2s infinite ease-in-out both; }
        .ldots span:nth-child(1){animation-delay:-0.3s} .ldots span:nth-child(2){animation-delay:-0.15s}
        @keyframes ldot { 0%,80%,100%{transform:scale(0);opacity:.4} 40%{transform:scale(1);opacity:1} }
        .thinking-label { font-size: 11px; color: var(--accent); font-weight: 500; display: flex; align-items: center; gap: 6px; font-family: 'DM Mono', monospace; animation: blinkAnim 1s infinite; }
        @keyframes blinkAnim { 0%,100%{opacity:1} 50%{opacity:.4} }
        .complexity-bar-wrap { display: flex; align-items: center; gap: 6px; width: 100%; }
        .complexity-bar { flex: 1; height: 3px; background: rgba(99,102,241,0.1); border-radius: 2px; overflow: hidden; }
        .complexity-fill { height: 100%; border-radius: 2px; background: linear-gradient(90deg, #06b6d4, #6366f1, #8b5cf6); transition: width 0.6s ease; }

        /* ── Input Zone ── */
        .input-zone { padding: 12px 28px 16px; background: var(--input-zone-bg); backdrop-filter: blur(12px); border-top: 1px solid var(--border); flex-shrink: 0; }
        .input-shell { position: relative; border-radius: 16px; padding: 2px; background: linear-gradient(135deg, rgba(99,102,241,0.5) 0%, rgba(6,182,212,0.3) 50%, rgba(139,92,246,0.4) 100%); animation: shellPulse 4s ease-in-out infinite; transition: background 0.3s; }
        @keyframes shellPulse { 0%,100%{background:linear-gradient(135deg,rgba(99,102,241,0.5) 0%,rgba(6,182,212,0.3) 50%,rgba(139,92,246,0.4) 100%)} 50%{background:linear-gradient(135deg,rgba(139,92,246,0.5) 0%,rgba(99,102,241,0.3) 50%,rgba(6,182,212,0.5) 100%)} }
        .scanner-line { position: absolute; left: 0; right: 0; height: 1px; background: linear-gradient(90deg,transparent,rgba(99,102,241,0.5),transparent); animation: scan 3s linear infinite; pointer-events: none; border-radius: 16px; }
        @keyframes scan { 0%{top:2px;opacity:0} 10%{opacity:1} 90%{opacity:1} 100%{top:calc(100% - 2px);opacity:0} }
        .corner-tl,.corner-tr,.corner-bl,.corner-br { position: absolute; width: 10px; height: 10px; border-color: rgba(99,102,241,0.7); border-style: solid; pointer-events: none; }
        .corner-tl{top:4px;left:4px;border-width:1.5px 0 0 1.5px;border-radius:3px 0 0 0}
        .corner-tr{top:4px;right:4px;border-width:1.5px 1.5px 0 0;border-radius:0 3px 0 0}
        .corner-bl{bottom:4px;left:4px;border-width:0 0 1.5px 1.5px;border-radius:0 0 0 3px}
        .corner-br{bottom:4px;right:4px;border-width:0 1.5px 1.5px 0;border-radius:0 0 3px 0}
        .input-inner { border-radius: 14px; background: var(--surface); padding: 12px 14px 10px; display: flex; flex-direction: column; gap: 10px; }
        .text-row { display: flex; align-items: flex-end; gap: 10px; }
        .prompt-prefix { font-family: 'DM Mono', monospace; font-size: 14px; color: #6366f1; padding-bottom: 3px; flex-shrink: 0; user-select: none; opacity: 0.8; }
        .input-textarea { flex: 1; background: transparent; border: none; outline: none; color: var(--text); font-family: 'DM Sans', sans-serif; font-size: 14.5px; line-height: 1.5; resize: none; min-height: 24px; max-height: 140px; overflow-y: auto; scrollbar-width: none; caret-color: #6366f1; }
        .input-textarea::placeholder { color: rgba(107,114,128,0.55); }
        .send-btn { width: 40px; height: 40px; border-radius: 11px; border: none; background: var(--accent); color: #fff; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; position: relative; overflow: hidden; transition: transform 0.15s, background 0.15s; }
        .send-btn::before { content:''; position: absolute; inset: 0; background: linear-gradient(135deg,rgba(255,255,255,0.15),transparent); }
        .send-btn:hover:not(:disabled){transform:scale(1.07);background:#818cf8}
        .send-btn:active:not(:disabled){transform:scale(0.96)}
        .send-btn:disabled{opacity:0.3;cursor:default}
        .send-btn svg{width:16px;height:16px}

        .kbd-hint { text-align: center; margin-top: 8px; display: flex; align-items: center; justify-content: center; gap: 6px; font-size: 10.5px; font-family: 'DM Mono', monospace; color: rgba(107,114,128,0.35); }
        .kbd { display: inline-flex; align-items: center; padding: 1px 5px; border: 1px solid rgba(107,114,128,0.2); border-radius: 3px; font-size: 10px; color: var(--muted); background: var(--kbd-bg); }

        .icon-btn {
          width: 32px; height: 32px; border-radius: 8px; border: 1px solid transparent; background: transparent; color: var(--muted); cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s;
        }
        .icon-btn:hover { background: var(--icon-btn-hover); color: var(--text); border-color: var(--icon-btn-border); }
        .icon-btn svg { width: 18px; height: 18px; }

        .icon-btn.recording {
          color: #ef4444 !important;
          animation: pulse-red 1.5s infinite;
        }
        @keyframes pulse-red {
          0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); background: rgba(239, 68, 68, 0.1); }
          70% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); background: rgba(239, 68, 68, 0.1); }
          100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); background: transparent; }
        }

        .attachments-list {
          display: flex; gap: 8px; padding: 0 16px 12px; flex-wrap: wrap; margin-top: -6px;
        }
        .attachment-chip {
          display: flex; align-items: center; gap: 6px; 
          background: var(--chip-bg); border: 1px solid var(--border); 
          padding: 5px 8px; border-radius: 6px; font-size: 11px;
        }
        .attachment-name {
          max-width: 100px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
        }
        .attachment-remove {
          background: none; border: none; color: var(--muted); cursor: pointer; display: flex; align-items: center; padding: 0;
        }
        .attachment-remove:hover { color: #f87171; }

        @media (max-width: 700px) { .page{grid-template-columns:1fr} .sidebar{display:none} }
        @keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
      `}</style>

      <div className="page">
        <aside className="sidebar">
          <div className="sidebar-top">
            <div className="logo" onClick={() => router.push("/")}>APEX<em>AI</em></div>
            <button className="new-btn" onClick={() => setMessages([])}>
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              New conversation
            </button>
          </div>

          <div className="bot-showcase">
            <div className="bot-wrap"><ApexBot mood={botMood} /></div>
            <div className="bot-name">APEX BOT</div>
            <div className="bot-status">
              <div className="live-dot" />
              {botMood === "thinking" ? "Processing..." : botMood === "celebrating" ? "Celebrating!" : "Online"}
            </div>
          </div>

          <div className="panel">
            <div className="panel-title">Routing Mode</div>
            <div className="panel-row"><div className="dot-on" />Librarian active</div>
            <div className="panel-row"><div className="dot-on" />Bandit standby</div>
            <div className="panel-row"><div className="dot-on" />Vector cache on</div>
            <div className="panel-row">
              <div className="dot-on" style={{ background: "#f59e0b", boxShadow: "0 0 5px #f59e0b" }} />
              Cascading fallback
            </div>
          </div>

          <div className="sidebar-bottom">
            <button className="back-btn" onClick={() => router.push("/")}>← Back to home</button>
          </div>
        </aside>

        <main className="main">
          <div className="chat-header">
            <div className="header-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="10" rx="2"/>
                <circle cx="12" cy="5" r="2"/>
                <path d="M12 7v4"/>
                <line x1="8" y1="16" x2="8.01" y2="16"/>
                <line x1="16" y1="16" x2="16.01" y2="16"/>
              </svg>
            </div>
            <div>
              <div className="header-title">ApexAI Router</div>
              <div className="header-sub">Adaptive multi-model selection</div>
            </div>
            <div className="header-right">
              <button 
                className="icon-btn" 
                onClick={() => setTheme(t => t === "dark" ? "light" : "dark")}
                title="Toggle Theme"
                style={{ width: "28px", height: "28px", marginRight: "8px" }}
              >
                {theme === "dark" ? (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
                ) : (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
                )}
              </button>
              <div className="online-pill"><div className="live-dot" />Online</div>
            </div>
          </div>

          <div className="messages">
            {messages.map((msg) => (
              <div key={msg.id} className={`msg-row ${msg.role === "user" ? "user" : ""}`}>
                <div className={`avatar ${msg.role === "assistant" ? "ai" : "user-av"}`}>
                  {msg.role === "assistant" ? "AI" : "U"}
                </div>
                <div className="msg-body">
                  <div className={`bubble ${msg.role === "assistant" ? "ai" : "user"}`}>
                    {msg.role === "assistant" && !msg.isLoading && (
                      <button className={`bubble-copy ${copiedId === msg.id ? "copied" : ""}`} onClick={() => copyMessage(msg.id, msg.content)} title="Copy response">
                        {copiedId === msg.id ? (
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                        ) : (
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                          </svg>
                        )}
                      </button>
                    )}
                    {msg.isLoading ? (
                      <div>
                        <div className="thinking-label">
                          <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                          Routing your prompt...
                        </div>
                        <div className="ldots" style={{ marginTop: "8px" }}><span /><span /><span /></div>
                      </div>
                    ) : (
                      <span dangerouslySetInnerHTML={{ __html: formatContent(msg.content) }} />
                    )}
                  </div>

                  {msg.role === "assistant" && !msg.isLoading && msg.model && msg.routeInfo && (
                    <div className="route-strip">
                      <div className="tag model-tag">
                        <div className="dot" style={{ background: modelColors[msg.model] || "#6366f1", boxShadow: `0 0 5px ${modelColors[msg.model] || "#6366f1"}` }} />
                        {msg.model}
                      </div>
                      <div className="tag">Tier {msg.routeInfo.tier}</div>
                      <div className="tag">{msg.routeInfo.category} · {msg.routeInfo.complexity}</div>
                      <div className="tag">
                        <svg viewBox="0 0 24 24" width="10" height="10" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                        {msg.latency}ms
                      </div>
                      <div className="tag">
                        <svg viewBox="0 0 24 24" width="10" height="10" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                        ${msg.cost}
                      </div>
                      {msg.routeInfo.cacheHit && <div className="tag cache-hit">⚡ cache hit</div>}
                      {msg.routeInfo.usedBandit && <div className="tag bandit-used">🎰 bandit</div>}
                      <div style={{ display: "flex", alignItems: "center", gap: "4px", marginLeft: "auto" }}>
                        <div className="complexity-bar-wrap" style={{ width: "60px" }}>
                          <div className="complexity-bar">
                            <div className="complexity-fill" style={{ width: `${(msg.routeInfo.complexity / 10) * 100}%` }} />
                          </div>
                        </div>
                        <span style={{ fontSize: "10px", color: "var(--muted)", fontFamily: "'DM Mono', monospace" }}>{msg.routeInfo.complexity}</span>
                      </div>
                      <div className="feedback-row">
                        <button className={`fb-btn ${msg.feedback === "up" ? "up-active" : ""}`} onClick={() => handleFeedback(msg.id, "up")} title="Good">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
                        </button>
                        <button className={`fb-btn ${msg.feedback === "down" ? "dn-active" : ""}`} onClick={() => handleFeedback(msg.id, "down")} title="Poor">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-2"/></svg>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>

          <div className="input-zone">
            <div className="input-shell" ref={shellRef}>
              <div className="scanner-line" />
              <div className="corner-tl" /><div className="corner-tr" />
              <div className="corner-bl" /><div className="corner-br" />

              <div className="input-inner">
                <div className="text-row">
                  <span className="prompt-prefix">&gt;_</span>
                  <textarea
                    ref={textareaRef}
                    className="input-textarea"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKey}
                    onFocus={handleFocus}
                    onBlur={handleBlur}
                    placeholder={isRecording ? "Recording… click mic to stop" : "Message the intelligent router…"}
                    rows={1}
                    onInput={(e) => {
                      const t = e.target as HTMLTextAreaElement;
                      t.style.height = "auto";
                      t.style.height = Math.min(t.scrollHeight, 140) + "px";
                    }}
                  />
                  <button className="send-btn" onClick={sendMessage} disabled={isLoading || (!input.trim() && attachments.length === 0)}>
                    {isLoading ? (
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" style={{ animation: "spin 0.8s linear infinite" }}>
                        <circle cx="8" cy="8" r="6" stroke="white" strokeWidth="2" strokeLinecap="round" strokeDasharray="16 20" />
                      </svg>
                    ) : (
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
                      </svg>
                    )}
                  </button>
                </div>

                {attachments.length > 0 && (
                  <div className="attachments-list">
                    {attachments.map((file, i) => (
                      <div key={i} className="attachment-chip">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="12" height="12"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
                        <span className="attachment-name">{file.name}</span>
                        <button onClick={() => removeAttachment(i)} className="attachment-remove">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                <div className="actions-row" style={{ display: "flex", gap: "8px", padding: "0 16px 12px" }}>
                  <input type="file" ref={fileInputRef} style={{ display: "none" }} onChange={handleFileChange} multiple />
                  <button className="icon-btn" title="Attach file" onClick={() => fileInputRef.current?.click()}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                      <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
                    </svg>
                  </button>
                  <button className={`icon-btn ${isRecording ? "recording" : ""}`} title="Voice input" onClick={toggleRecording}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                      <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                      <line x1="12" y1="19" x2="12" y2="23"/>
                      <line x1="8" y1="23" x2="16" y2="23"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            <div className="kbd-hint">
              <span className="kbd">↵</span> send &nbsp;·&nbsp;
              <span className="kbd">⇧↵</span> newline
            </div>
          </div>
        </main>
      </div>
    </>
  );
}