import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
    LayoutDashboard, GitBranch, AlertTriangle, Zap,
    Wrench, Brain, ArrowLeft, Home
} from 'lucide-react';

const navItems = [
    { path: '/app', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/app/analyze', icon: GitBranch, label: 'Analyze Repo' },
    { path: '/app/risks', icon: AlertTriangle, label: 'Risk Map' },
    { path: '/app/chaos', icon: Zap, label: 'Chaos Tests' },
    { path: '/app/fixes', icon: Wrench, label: 'Fix Suggestions' },
];

export default function Sidebar() {
    const navigate = useNavigate();

    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <div className="sidebar-logo" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
                    <div className="logo-icon">
                        <Brain size={20} color="white" />
                    </div>
                    <div>
                        <h1>Cerebro Chaos</h1>
                        <span>AI Reliability Engineer</span>
                    </div>
                </div>
            </div>

            <nav className="sidebar-nav">
                <button className="nav-back-btn" onClick={() => navigate('/')}>
                    <ArrowLeft size={16} />
                    Back to Home
                </button>
                <div className="nav-divider" />
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                        end={item.path === '/app'}
                    >
                        <item.icon className="nav-icon" size={18} />
                        {item.label}
                    </NavLink>
                ))}
            </nav>

            <div style={{ padding: 'var(--space-md)', borderTop: '1px solid var(--border-subtle)' }}>
                <div style={{
                    padding: 'var(--space-md)',
                    background: 'linear-gradient(135deg, rgba(108,61,232,0.1), rgba(34,211,238,0.05))',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-subtle)',
                }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                        Powered by
                    </div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-400)' }}>
                        🔴 AMD ROCm + GPU
                    </div>
                </div>
            </div>
        </aside>
    );
}
