"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

const FeatureIcons = {
  Router: (props: any) => (<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M4 11V9a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v2"/><path d="M4 19v-2a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v2"/><path d="M4 15h16"/><path d="M12 3v4"/><path d="M12 15v4"/></svg>),
  Cache: (props: any) => (<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...props}><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>),
  Selector: (props: any) => (<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...props}><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>),
  Fallback: (props: any) => (<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M21 2v6h-6"/><path d="M3 12a9 9 0 1 0 2.13-5.88L21 8"/></svg>),
  Cost: (props: any) => (<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...props}><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>),
};

export default function LandingPage() {
  const router = useRouter();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePos({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const particles: { x: number; y: number; vx: number; vy: number; size: number; baseAlpha: number }[] = [];
    for (let i = 0; i < 60; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.15,
        vy: (Math.random() - 0.5) * 0.15,
        size: Math.random() * 1.5 + 0.5,
        baseAlpha: Math.random() * 0.4 + 0.1,
      });
    }

    let animId: number;
    function draw() {
      if (!ctx || !canvas) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      const isLight = document.documentElement.getAttribute('data-theme') === 'light';

      particles.forEach((p, i) => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = isLight ? `rgba(59, 130, 246, ${p.baseAlpha})` : `rgba(180, 200, 255, ${p.baseAlpha})`;
        ctx.fill();

        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[j].x - p.x;
          const dy = particles[j].y - p.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 150) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = isLight ? `rgba(59, 130, 246, ${0.08 * (1 - dist / 150)})` : `rgba(120, 160, 255, ${0.05 * (1 - dist / 150)})`;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      });
      animId = requestAnimationFrame(draw);
    }
    draw();

    const handleResize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", handleResize);
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Space+Grotesk:wght@500;700&display=swap');

        :root {
          --bg: #030508;
          --text-main: #f0f4f8;
          --text-muted: #8b9bb4;
          --accent-1: #3b82f6;
          --accent-2: #8b5cf6;
          --glass-bg: rgba(15, 23, 42, 0.4);
          --glass-border: rgba(255, 255, 255, 0.06);
          --aura-color-1: rgba(59, 130, 246, 0.08);
          --aura-color-2: rgba(139, 92, 246, 0.05);
          --bot-body: rgba(30, 41, 59, 1);
          --bot-border: rgba(255, 255, 255, 0.12);
          --nav-bg: rgba(3, 5, 8, 0.5);
          --card-hover-bg: rgba(30, 41, 59, 0.6);
        }

        :root[data-theme="light"] {
          --bg: #f8fafc;
          --text-main: #0f172a;
          --text-muted: #64748b;
          --accent-1: #3b82f6;
          --accent-2: #8b5cf6;
          --glass-bg: rgba(255, 255, 255, 0.6);
          --glass-border: rgba(0, 0, 0, 0.06);
          --aura-color-1: rgba(59, 130, 246, 0.06);
          --aura-color-2: rgba(139, 92, 246, 0.04);
          --bot-body: rgba(241, 245, 249, 1);
          --bot-border: rgba(0, 0, 0, 0.1);
          --nav-bg: rgba(248, 250, 252, 0.5);
          --card-hover-bg: rgba(241, 245, 249, 0.8);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
          background: var(--bg);
          color: var(--text-main);
          font-family: 'Inter', sans-serif;
          overflow-x: hidden;
          -webkit-font-smoothing: antialiased;
        }

        /* Abstract dynamic aura following mouse or centered */
        .aura-container {
          position: fixed;
          inset: 0;
          overflow: hidden;
          z-index: 0;
          pointer-events: none;
        }
        
        .aura {
          position: absolute;
          width: 800px;
          height: 800px;
          border-radius: 50%;
          background: radial-gradient(circle, var(--aura-color-1) 0%, var(--aura-color-2) 40%, transparent 70%);
          filter: blur(60px);
          transform: translate(-50%, -50%);
          transition: left 0.8s cubic-bezier(0.2, 0.8, 0.2, 1), top 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);
        }

        canvas {
          position: fixed;
          top: 0; left: 0;
          z-index: 0;
          pointer-events: none;
        }

        .landing-wrap {
          position: relative;
          z-index: 2;
          min-height: 100vh;
          display: flex;
          flex-direction: column;
        }

        nav {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 24px 48px;
          border-bottom: 1px solid var(--glass-border);
          background: var(--nav-bg);
          backdrop-filter: blur(12px);
          position: sticky;
          top: 0;
          z-index: 100;
          animation: fadeDown 0.8s ease backwards;
        }

        .logo {
          font-family: 'Space Grotesk', sans-serif;
          font-weight: 700;
          font-size: 20px;
          color: var(--text-main);
          letter-spacing: -0.5px;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .logo span {
          color: var(--accent-1);
        }

        .nav-links {
          display: flex;
          gap: 32px;
          font-size: 14px;
          font-weight: 500;
          color: var(--text-muted);
        }

        .nav-links a {
          cursor: pointer;
          transition: color 0.3s;
        }
        .nav-links a:hover {
          color: var(--text-main);
        }
        
        .theme-toggle-btn {
          width: 32px;
          height: 32px;
          border-radius: 8px;
          border: 1px solid transparent;
          background: transparent;
          color: var(--text-muted);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s;
        }
        .theme-toggle-btn:hover {
          background: var(--glass-bg);
          color: var(--text-main);
          border-color: var(--glass-border);
        }
        .theme-toggle-btn svg {
          width: 18px;
          height: 18px;
        }

        .hero-section {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
          padding: 40px 20px;
          max-width: 900px;
          margin: 0 auto;
        }

        .pill {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          background: rgba(59, 130, 246, 0.05);
          border: 1px solid rgba(59, 130, 246, 0.2);
          border-radius: 100px;
          padding: 6px 16px;
          font-size: 12px;
          font-weight: 600;
          letter-spacing: 0.5px;
          color: #60a5fa;
          margin-bottom: 32px;
          animation: fadeUp 0.8s ease 0.1s backwards;
        }

        .pill-dot {
          width: 6px; height: 6px;
          background: #60a5fa;
          border-radius: 50%;
          box-shadow: 0 0 8px #60a5fa;
        }

        .hero-title {
          font-family: 'Space Grotesk', sans-serif;
          font-size: clamp(40px, 6vw, 76px);
          font-weight: 700;
          line-height: 1.1;
          letter-spacing: -1.5px;
          color: var(--text-main);
          margin-bottom: 24px;
          animation: fadeUp 0.8s ease 0.2s backwards;
        }

        .hero-title .gradient-text {
          background: linear-gradient(135deg, #f0f4f8 0%, #a5b4fc 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .hero-subtitle {
          font-size: clamp(16px, 2vw, 18px);
          line-height: 1.6;
          color: var(--text-muted);
          max-width: 600px;
          margin-bottom: 48px;
          font-weight: 400;
          animation: fadeUp 0.8s ease 0.3s backwards;
        }

        .cta-btn {
          position: relative;
          background: var(--text-main);
          color: var(--bg);
          border: none;
          border-radius: 8px;
          padding: 16px 40px;
          font-family: 'Space Grotesk', sans-serif;
          font-size: 15px;
          font-weight: 600;
          cursor: pointer;
          overflow: hidden;
          transition: transform 0.2s, box-shadow 0.2s;
          display: inline-flex;
          align-items: center;
          gap: 12px;
          animation: fadeUp 0.8s ease 0.4s backwards;
        }

        .cta-btn::before {
          content: "";
          position: absolute;
          top: 0; left: 0; width: 100%; height: 100%;
          background: linear-gradient(120deg, transparent, rgba(255,255,255,0.3), transparent);
          transform: translateX(-100%);
          transition: transform 0.6s;
        }

        .cta-btn:hover {
          transform: translateY(-2px);
          box-shadow: 0 10px 25px -5px rgba(255,255,255,0.1);
        }

        .cta-btn:hover::before {
          transform: translateX(100%);
        }

        .cta-btn svg {
          width: 18px;
          height: 18px;
          transition: transform 0.3s;
        }
        .cta-btn:hover svg {
          transform: translateX(4px);
        }

        .features-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 20px;
          width: 100%;
          max-width: 1000px;
          margin-top: 80px;
          animation: fadeUp 0.8s ease 0.5s backwards;
        }

        .feature-card {
          background: var(--glass-bg);
          border: 1px solid var(--glass-border);
          border-radius: 12px;
          padding: 24px;
          text-align: left;
          backdrop-filter: blur(10px);
          transition: background 0.3s, border-color 0.3s, transform 0.3s;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .feature-card:hover {
          background: var(--card-hover-bg);
          border-color: rgba(96, 165, 250, 0.3);
          transform: translateY(-4px);
        }

        .feature-icon-wrap {
          width: 40px;
          height: 40px;
          border-radius: 8px;
          background: rgba(96, 165, 250, 0.1);
          color: #60a5fa;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .feature-icon-wrap svg {
          width: 20px;
          height: 20px;
        }

        .feature-title {
          font-family: 'Space Grotesk', sans-serif;
          font-weight: 500;
          font-size: 15px;
          color: var(--text-main);
        }

        .feature-desc {
          font-size: 13px;
          color: var(--text-muted);
          line-height: 1.5;
        }

        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes fadeDown {
          from { opacity: 0; transform: translateY(-20px); }
          to { opacity: 1; transform: translateY(0); }
        }

        /* Cute Bot Animations */
        .cute-bot {
          position: relative;
          margin-bottom: -15px;
          animation: floatBot 4s ease-in-out infinite;
          z-index: 10;
        }

        .bot-glow {
          position: absolute;
          inset: -20px;
          background: radial-gradient(circle, rgba(59, 130, 246, 0.25) 0%, transparent 70%);
          border-radius: 50%;
          animation: pulseGlow 3s ease-in-out infinite;
          z-index: -1;
        }

        @keyframes floatBot {
          0%, 100% { transform: translateY(0px) rotate(0deg); }
          50% { transform: translateY(-12px) rotate(2deg); }
        }

        @keyframes pulseGlow {
          0%, 100% { opacity: 0.5; transform: scale(1); }
          50% { opacity: 1; transform: scale(1.1); }
        }

        .bot-head-group {
          animation: headBob 4s ease-in-out infinite;
          transform-origin: 50px 50px;
        }
        @keyframes headBob {
          0%, 100% { transform: rotate(0deg); }
          50% { transform: rotate(-3deg); }
        }

        .bot-eyes {
          animation: blinkBot 5s infinite;
          transform-origin: 50px 48px;
        }
        @keyframes blinkBot {
          0%, 94%, 100% { transform: scaleY(1); }
          96% { transform: scaleY(0.1); }
        }

        .bot-flame {
          animation: flicker 0.1s infinite alternate;
          transform-origin: 50px 100px;
        }
        .bot-flame-inner {
          animation: flicker 0.1s infinite alternate-reverse;
          transform-origin: 50px 100px;
        }
        @keyframes flicker {
          0% { transform: scaleY(1) scaleX(1); opacity: 0.8; }
          100% { transform: scaleY(1.2) scaleX(0.9); opacity: 1; }
        }

        .bot-arm-l { animation: floatArmL 4s ease-in-out infinite; }
        .bot-arm-r { animation: floatArmR 4s ease-in-out infinite; }
        @keyframes floatArmL { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-4px); } }
        @keyframes floatArmR { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
        
        .bot-antenna-dot { animation: antennaBlink 2s infinite; }
        @keyframes antennaBlink {
          0%, 100% { fill: #3b82f6; filter: drop-shadow(0 0 4px #3b82f6); }
          50% { fill: #8b5cf6; filter: drop-shadow(0 0 8px #8b5cf6); }
        }

        @media (max-width: 768px) {
          nav { padding: 20px; }
          .nav-links { display: none; }
          .features-grid { grid-template-columns: 1fr; margin-top: 60px; }
        }
      `}</style>

      <div className="aura-container">
        <div 
          className="aura" 
          style={{ 
            left: mousePos.x || '50%', 
            top: mousePos.y || '50%' 
          }} 
        />
      </div>

      <canvas ref={canvasRef} />

      <div className="landing-wrap">
        <nav>
          <div className="logo">
            APEX<span>AI</span>
          </div>
          <button 
            className="theme-toggle-btn" 
            onClick={() => setTheme(t => t === "dark" ? "light" : "dark")}
            title="Toggle Theme"
          >
            {theme === "dark" ? (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
            ) : (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
            )}
          </button>
        </nav>

        <main className="hero-section">
          <div className="pill">
            <div className="pill-dot" />
            Adaptive Routing Active
          </div>

          <div className="cute-bot">
            <div className="bot-glow" />
            <svg viewBox="0 0 100 120" width="90" height="108" fill="none">
               {/* Thruster Flame */}
               <path d="M42 100 Q50 125 58 100 Z" fill="#3b82f6" className="bot-flame" />
               <path d="M46 100 Q50 115 54 100 Z" fill="#93c5fd" className="bot-flame-inner" />
               
               {/* Body */}
               <path d="M30 85 C30 75, 70 75, 70 85 C70 98, 60 105, 50 105 C40 105, 30 98, 30 85 Z" fill="var(--bot-body)" stroke="var(--bot-border)" strokeWidth="1.5" />
               {/* Body accents */}
               <circle cx="50" cy="90" r="4" fill="#0f172a" />
               <circle cx="50" cy="90" r="2" fill="#3b82f6" opacity="0.8" />
               
               {/* Arms (floating) */}
               <rect x="18" y="76" width="8" height="20" rx="4" fill="var(--bot-body)" stroke="var(--bot-border)" className="bot-arm-l" />
               <rect x="74" y="76" width="8" height="20" rx="4" fill="var(--bot-body)" stroke="var(--bot-border)" className="bot-arm-r" />
               
               {/* Neck joint */}
               <rect x="46" y="65" width="8" height="12" fill="#0f172a" />
               
               <g className="bot-head-group">
                 {/* Head Outer */}
                 <rect x="20" y="30" width="60" height="40" rx="16" fill="var(--bot-body)" stroke="var(--bot-border)" strokeWidth="1.5" />
                 
                 {/* Face Plate Space */}
                 <rect x="26" y="36" width="48" height="22" rx="8" fill="#030508" stroke="rgba(59, 130, 246, 0.2)" />
                 
                 {/* Eyes */}
                 <g className="bot-eyes">
                   <path d="M36 48 Q40 43 44 48 Q40 45 36 48" stroke="#60a5fa" strokeWidth="2.5" strokeLinecap="round" />
                   <path d="M56 48 Q60 43 64 48 Q60 45 56 48" stroke="#60a5fa" strokeWidth="2.5" strokeLinecap="round" />
                   {/* Cheeks */}
                   <ellipse cx="32" cy="52" rx="3" ry="1.5" fill="#ef4444" opacity="0.3" />
                   <ellipse cx="68" cy="52" rx="3" ry="1.5" fill="#ef4444" opacity="0.3" />
                 </g>

                 {/* Antenna */}
                 <path d="M50 30 V15" stroke="#475569" strokeWidth="2" strokeLinecap="round" />
                 <circle cx="50" cy="12" r="4" fill="#3b82f6" className="bot-antenna-dot" />
               </g>
            </svg>
          </div>

          <h1 className="hero-title">
            Intelligence, Routed <br />
            <span className="gradient-text">with Precision.</span>
          </h1>

          <p className="hero-subtitle">
            Multi-model adaptive routing with semantic caching and real-time bandit-driven model selection. Built for performance, tailored for efficiency.
          </p>

          <button className="cta-btn" onClick={() => router.push('/chat')}>
            Launch System
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14" />
              <path d="m12 5 7 7-7 7" />
            </svg>
          </button>

          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon-wrap"><FeatureIcons.Router /></div>
              <div className="feature-title">Librarian Router</div>
              <div className="feature-desc">Context-aware dynamic routing ensuring the best model handles every request seamlessly.</div>
            </div>
            <div className="feature-card">
              <div className="feature-icon-wrap"><FeatureIcons.Cache /></div>
              <div className="feature-title">Vector Cache</div>
              <div className="feature-desc">Sub-millisecond semantic retrieval built on pgVector minimizes redundant compute.</div>
            </div>
            <div className="feature-card">
              <div className="feature-icon-wrap"><FeatureIcons.Selector /></div>
              <div className="feature-title">Bandit Selection</div>
              <div className="feature-desc">Reinforcement learning optimizes model selection balancing cost, latency, and quality.</div>
            </div>
            <div className="feature-card">
              <div className="feature-icon-wrap"><FeatureIcons.Fallback /></div>
              <div className="feature-title">Cascading Fallbacks</div>
              <div className="feature-desc">Zero downtime architecture seamlessly rolls over to backup models on failure.</div>
            </div>
            <div className="feature-card">
              <div className="feature-icon-wrap"><FeatureIcons.Cost /></div>
              <div className="feature-title">Cost Optimizer</div>
              <div className="feature-desc">Real-time expenditure tracking with automatic lightweight model tiering.</div>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}