import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Brain, GitBranch, AlertTriangle, Zap, Wrench, Shield,
    ArrowRight, ChevronRight, Cpu, Activity, BarChart3,
    Globe, Lock, Layers, Sparkles, Play, Star, Check,
    Github, Eye, Target, Gauge
} from 'lucide-react';

const FEATURES = [
    {
        icon: GitBranch,
        title: 'Deep Code Analysis',
        description: 'Parse any GitHub repository to map service architectures, dependency graphs, and interconnection patterns automatically.',
        color: '#7c5aff',
        gradient: 'linear-gradient(135deg, #7c5aff, #9b7aff)',
    },
    {
        icon: AlertTriangle,
        title: 'AI Risk Detection',
        description: 'Identify single points of failure, missing retry logic, cascading failure risks, and reliability blind spots with AI.',
        color: '#ff3366',
        gradient: 'linear-gradient(135deg, #ff3366, #ff6b8a)',
    },
    {
        icon: Zap,
        title: 'Chaos Simulation',
        description: 'Run latency injection, service failures, network partitions, and resource exhaustion tests virtually — no prod impact.',
        color: '#fbbf24',
        gradient: 'linear-gradient(135deg, #fbbf24, #f59e0b)',
    },
    {
        icon: Wrench,
        title: 'Auto-Fix Generation',
        description: 'Get production-ready code fixes with health checks, circuit breakers, retry logic, and redundancy patterns.',
        color: '#10b981',
        gradient: 'linear-gradient(135deg, #10b981, #34d399)',
    },
];

const STEPS = [
    { num: '01', title: 'Connect Repository', desc: 'Paste any GitHub URL and select the branch to analyze.', icon: Github },
    { num: '02', title: 'AI Scans Architecture', desc: 'Our engine maps services, dependencies, and failure domains.', icon: Eye },
    { num: '03', title: 'Detect & Simulate', desc: 'AI detects risks and runs chaos simulations on your architecture.', icon: Target },
    { num: '04', title: 'Fix & Harden', desc: 'Get auto-generated fixes to eliminate reliability blind spots.', icon: Shield },
];

const STATS = [
    { value: '40+', label: 'Risk Patterns', icon: AlertTriangle },
    { value: '5', label: 'Chaos Modes', icon: Zap },
    { value: '99.9%', label: 'Accuracy', icon: Target },
    { value: '<30s', label: 'Analysis Time', icon: Gauge },
];

export default function HomePage() {
    const navigate = useNavigate();
    const [scrollY, setScrollY] = useState(0);
    const [visibleSections, setVisibleSections] = useState(new Set());

    useEffect(() => {
        const handleScroll = () => setScrollY(window.scrollY);
        window.addEventListener('scroll', handleScroll, { passive: true });
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        setVisibleSections((prev) => new Set([...prev, entry.target.id]));
                    }
                });
            },
            { threshold: 0.15 }
        );
        document.querySelectorAll('[data-animate]').forEach((el) => observer.observe(el));
        return () => observer.disconnect();
    }, []);

    return (
        <div className="home-page">
            {/* ── Navbar ─────────────────────────────── */}
            <nav className="home-nav" style={{ background: scrollY > 60 ? 'rgba(8,8,24,0.92)' : 'transparent', backdropFilter: scrollY > 60 ? 'blur(20px)' : 'none' }}>
                <div className="home-nav-inner">
                    <div className="home-logo" onClick={() => navigate('/')}>
                        <div className="home-logo-icon">
                            <Brain size={22} color="white" />
                        </div>
                        <span className="home-logo-text">Cerebro Chaos</span>
                    </div>
                    <div className="home-nav-links">
                        <a href="#features">Features</a>
                        <a href="#how-it-works">How It Works</a>
                        <a href="#stats">Metrics</a>
                    </div>
                    <div className="home-nav-actions">
                        <button className="btn-nav-ghost" onClick={() => navigate('/app')}>Dashboard</button>
                        <button className="btn-nav-primary" onClick={() => navigate('/app/analyze')}>
                            <Sparkles size={16} />
                            Launch App
                        </button>
                    </div>
                </div>
            </nav>

            {/* ── Hero Section ──────────────────────── */}
            <section className="hero-section">
                <div className="hero-bg-effects">
                    <div className="hero-orb hero-orb-1" />
                    <div className="hero-orb hero-orb-2" />
                    <div className="hero-orb hero-orb-3" />
                    <div className="hero-grid-overlay" />
                </div>

                <div className="hero-content">
                    <div className="hero-badge">
                        <Cpu size={14} />
                        <span>Powered by AMD ROCm + GPU Acceleration</span>
                        <ChevronRight size={14} />
                    </div>

                    <h1 className="hero-title">
                        <span className="hero-title-line">Predict system failures</span>
                        <span className="hero-title-accent">before they hit production</span>
                    </h1>

                    <p className="hero-subtitle">
                        Cerebro Chaos is your AI Reliability Engineer — it analyzes codebases,
                        detects architectural risks, runs chaos simulations, and generates fixes.
                        All from a single GitHub URL.
                    </p>

                    <div className="hero-actions">
                        <button className="btn-hero-primary" onClick={() => navigate('/app/analyze')}>
                            <Play size={18} />
                            Start Analyzing
                            <ArrowRight size={18} />
                        </button>
                        <button className="btn-hero-secondary" onClick={() => navigate('/app')}>
                            <BarChart3 size={18} />
                            View Dashboard
                        </button>
                    </div>

                    <div className="hero-trust">
                        <div className="hero-trust-avatars">
                            {['🧠', '⚡', '🛡️', '🔧'].map((e, i) => (
                                <div key={i} className="trust-avatar" style={{ animationDelay: `${i * 100}ms` }}>{e}</div>
                            ))}
                        </div>
                        <span>Trusted by reliability engineers worldwide</span>
                    </div>
                </div>

                {/* Hero Visual - Floating Dashboard Preview */}
                <div className="hero-visual">
                    <div className="hero-card hero-card-main">
                        <div className="hc-header">
                            <div className="hc-dots">
                                <span className="dot red" /><span className="dot yellow" /><span className="dot green" />
                            </div>
                            <span className="hc-title">cerebro-chaos — analysis</span>
                        </div>
                        <div className="hc-body">
                            <div className="hc-stat-row">
                                <div className="hc-stat"><span className="hc-val critical">28</span><span className="hc-label">Critical</span></div>
                                <div className="hc-stat"><span className="hc-val warning">12</span><span className="hc-label">Medium</span></div>
                                <div className="hc-stat"><span className="hc-val success">85</span><span className="hc-label">Services</span></div>
                            </div>
                            <div className="hc-graph-preview">
                                {[...Array(12)].map((_, i) => (
                                    <div key={i} className="hc-node" style={{
                                        left: `${10 + (i % 4) * 25}%`,
                                        top: `${15 + Math.floor(i / 4) * 30}%`,
                                        animationDelay: `${i * 150}ms`
                                    }}>
                                        <div className="hc-node-dot" />
                                    </div>
                                ))}
                                <svg className="hc-edges" viewBox="0 0 300 150" style={{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0 }}>
                                    <line x1="45" y1="35" x2="115" y2="35" stroke="rgba(108,61,232,0.3)" strokeWidth="1" />
                                    <line x1="115" y1="35" x2="185" y2="35" stroke="rgba(34,211,238,0.3)" strokeWidth="1" />
                                    <line x1="45" y1="35" x2="45" y2="75" stroke="rgba(108,61,232,0.2)" strokeWidth="1" />
                                    <line x1="115" y1="35" x2="115" y2="75" stroke="rgba(255,51,102,0.3)" strokeWidth="1" />
                                    <line x1="185" y1="35" x2="255" y2="75" stroke="rgba(34,211,238,0.2)" strokeWidth="1" />
                                    <line x1="45" y1="75" x2="115" y2="115" stroke="rgba(251,191,36,0.3)" strokeWidth="1" />
                                    <line x1="185" y1="75" x2="255" y2="115" stroke="rgba(16,185,129,0.3)" strokeWidth="1" />
                                </svg>
                            </div>
                        </div>
                    </div>

                    <div className="hero-card hero-card-float hero-card-risk">
                        <AlertTriangle size={16} color="#ff3366" />
                        <div>
                            <div className="hcf-title">Single Point of Failure</div>
                            <div className="hcf-sub">signals module — 95% risk</div>
                        </div>
                    </div>

                    <div className="hero-card hero-card-float hero-card-fix">
                        <Check size={16} color="#10b981" />
                        <div>
                            <div className="hcf-title">Fix Generated</div>
                            <div className="hcf-sub">Add health checks + retry</div>
                        </div>
                    </div>
                </div>
            </section>

            {/* ── Features Section ──────────────────── */}
            <section className="features-section" id="features" data-animate>
                <div className="section-container">
                    <div className={`section-header ${visibleSections.has('features') ? 'visible' : ''}`}>
                        <div className="section-badge">
                            <Layers size={14} />
                            Core Capabilities
                        </div>
                        <h2>Everything you need to build <span className="text-gradient">resilient systems</span></h2>
                        <p>From code analysis to chaos simulation — Cerebro Chaos covers the full reliability lifecycle.</p>
                    </div>

                    <div className="features-grid">
                        {FEATURES.map((f, i) => (
                            <div
                                key={i}
                                className={`feature-card ${visibleSections.has('features') ? 'visible' : ''}`}
                                style={{ transitionDelay: `${i * 100}ms` }}
                            >
                                <div className="feature-icon-wrap" style={{ background: f.gradient }}>
                                    <f.icon size={24} color="white" />
                                </div>
                                <h3>{f.title}</h3>
                                <p>{f.description}</p>
                                <div className="feature-link">
                                    Learn more <ArrowRight size={14} />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ── How It Works Section ──────────────── */}
            <section className="how-section" id="how-it-works" data-animate>
                <div className="section-container">
                    <div className={`section-header ${visibleSections.has('how-it-works') ? 'visible' : ''}`}>
                        <div className="section-badge">
                            <Activity size={14} />
                            Workflow
                        </div>
                        <h2>Analyze any repo in <span className="text-gradient">four simple steps</span></h2>
                        <p>From GitHub URL to actionable reliability insights in under 30 seconds.</p>
                    </div>

                    <div className="steps-grid">
                        {STEPS.map((s, i) => (
                            <div
                                key={i}
                                className={`step-card ${visibleSections.has('how-it-works') ? 'visible' : ''}`}
                                style={{ transitionDelay: `${i * 120}ms` }}
                            >
                                <div className="step-number">{s.num}</div>
                                <div className="step-icon-wrap">
                                    <s.icon size={28} />
                                </div>
                                <h4>{s.title}</h4>
                                <p>{s.desc}</p>
                                {i < STEPS.length - 1 && <div className="step-connector" />}
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ── Stats Section ─────────────────────── */}
            <section className="stats-section" id="stats" data-animate>
                <div className="section-container">
                    <div className="stats-bar">
                        {STATS.map((s, i) => (
                            <div key={i} className={`stat-item ${visibleSections.has('stats') ? 'visible' : ''}`} style={{ transitionDelay: `${i * 80}ms` }}>
                                <s.icon size={20} className="stat-item-icon" />
                                <div className="stat-item-value">{s.value}</div>
                                <div className="stat-item-label">{s.label}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ── CTA Section ───────────────────────── */}
            <section className="cta-section" data-animate id="cta">
                <div className="section-container">
                    <div className={`cta-box ${visibleSections.has('cta') ? 'visible' : ''}`}>
                        <div className="cta-glow" />
                        <h2>Ready to make your systems <span className="text-gradient">unbreakable?</span></h2>
                        <p>Start analyzing your first repository — completely free. No setup required.</p>
                        <div className="cta-actions">
                            <button className="btn-hero-primary" onClick={() => navigate('/app/analyze')}>
                                <Sparkles size={18} />
                                Get Started Free
                                <ArrowRight size={18} />
                            </button>
                        </div>
                    </div>
                </div>
            </section>

            {/* ── Footer ────────────────────────────── */}
            <footer className="home-footer">
                <div className="section-container">
                    <div className="footer-inner">
                        <div className="footer-brand">
                            <div className="home-logo">
                                <div className="home-logo-icon small">
                                    <Brain size={16} color="white" />
                                </div>
                                <span className="home-logo-text">Cerebro Chaos</span>
                            </div>
                            <p>AI-Powered Reliability Engineering Platform</p>
                        </div>
                        <div className="footer-links">
                            <a href="#features">Features</a>
                            <a href="#how-it-works">How It Works</a>
                            <a onClick={() => navigate('/app')}>Dashboard</a>
                        </div>
                        <div className="footer-badge">
                            <span>Powered by</span>
                            <strong>🔴 AMD ROCm + GPU</strong>
                        </div>
                    </div>
                    <div className="footer-bottom">
                        <span>© 2026 Cerebro Chaos. Built for reliability engineers.</span>
                    </div>
                </div>
            </footer>
        </div>
    );
}
