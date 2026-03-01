import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Shield, AlertTriangle, Zap, GitBranch, TrendingUp,
    Activity, Brain, ArrowRight
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import api from '../services/api';

const SEVERITY_COLORS = {
    critical: '#ff3366',
    high: '#ff6b35',
    medium: '#fbbf24',
    low: '#34d399',
};

export default function Dashboard() {
    const [stats, setStats] = useState(null);
    const [repos, setRepos] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        loadData();
    }, []);

    async function loadData() {
        setLoading(true);
        try {
            const [statsData, reposData] = await Promise.all([
                api.getDashboardStats().catch(() => null),
                api.listRepos().catch(() => []),
            ]);
            setStats(statsData);
            setRepos(reposData || []);
        } catch (err) {
            console.error('Failed to load dashboard:', err);
        }
        setLoading(false);
    }

    const riskPieData = stats ? [
        { name: 'Critical', value: stats.risk_breakdown?.critical || 0, color: SEVERITY_COLORS.critical },
        { name: 'High', value: stats.risk_breakdown?.high || 0, color: SEVERITY_COLORS.high },
        { name: 'Medium', value: stats.risk_breakdown?.medium || 0, color: SEVERITY_COLORS.medium },
        { name: 'Low', value: stats.risk_breakdown?.low || 0, color: SEVERITY_COLORS.low },
    ].filter(d => d.value > 0) : [];

    return (
        <div className="fade-in">
            <div className="page-header">
                <h2>🧠 Command Center</h2>
                <p>AI-Powered Reliability Analysis Dashboard</p>
            </div>

            {/* Stats Grid */}
            <div className="stats-grid stagger">
                <div className="card stat-card primary">
                    <div className="stat-icon"><GitBranch size={40} /></div>
                    <div className="stat-value">{stats?.total_repos || 0}</div>
                    <div className="stat-label">Repositories</div>
                </div>
                <div className="card stat-card danger">
                    <div className="stat-icon"><AlertTriangle size={40} /></div>
                    <div className="stat-value">{stats?.total_risks || 0}</div>
                    <div className="stat-label">Risks Detected</div>
                </div>
                <div className="card stat-card warning">
                    <div className="stat-icon"><Zap size={40} /></div>
                    <div className="stat-value">{stats?.total_tests || 0}</div>
                    <div className="stat-label">Chaos Tests</div>
                </div>
                <div className="card stat-card success">
                    <div className="stat-icon"><Shield size={40} /></div>
                    <div className="stat-value">{Math.round((stats?.avg_failure_probability || 0) * 100)}%</div>
                    <div className="stat-label">Avg Failure Prob</div>
                </div>
            </div>

            <div className="grid-2" style={{ marginBottom: 'var(--space-xl)' }}>
                {/* Risk Breakdown Chart */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">📊 Risk Severity Breakdown</h3>
                    </div>
                    {riskPieData.length > 0 ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-lg)' }}>
                            <ResponsiveContainer width="50%" height={200}>
                                <PieChart>
                                    <Pie
                                        data={riskPieData}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={50}
                                        outerRadius={80}
                                        paddingAngle={4}
                                        dataKey="value"
                                    >
                                        {riskPieData.map((entry, i) => (
                                            <Cell key={i} fill={entry.color} stroke="transparent" />
                                        ))}
                                    </Pie>
                                </PieChart>
                            </ResponsiveContainer>
                            <div style={{ flex: 1 }}>
                                {riskPieData.map((item) => (
                                    <div key={item.name} style={{
                                        display: 'flex', alignItems: 'center', gap: '8px',
                                        marginBottom: '8px', fontSize: '0.875rem',
                                    }}>
                                        <div style={{
                                            width: '12px', height: '12px', borderRadius: '3px',
                                            background: item.color,
                                        }} />
                                        <span style={{ color: 'var(--text-secondary)', flex: 1 }}>{item.name}</span>
                                        <span style={{ fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{item.value}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="empty-state" style={{ padding: 'var(--space-xl)' }}>
                            <p>No risk data yet. Analyze a repository to start.</p>
                        </div>
                    )}
                </div>

                {/* Quick Actions */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">🚀 Quick Actions</h3>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
                        <button
                            className="btn btn-primary btn-lg"
                            style={{ width: '100%', justifyContent: 'center' }}
                            onClick={() => navigate('/analyze')}
                        >
                            <Brain size={20} />
                            Analyze New Repository
                            <ArrowRight size={16} />
                        </button>
                        <button
                            className="btn btn-ghost"
                            style={{ width: '100%', justifyContent: 'center' }}
                            onClick={() => navigate('/risks')}
                        >
                            <AlertTriangle size={18} />
                            View All Risks
                        </button>
                        <button
                            className="btn btn-ghost"
                            style={{ width: '100%', justifyContent: 'center' }}
                            onClick={() => navigate('/chaos')}
                        >
                            <Zap size={18} />
                            Run Chaos Tests
                        </button>
                    </div>

                    {/* Critical Risks Alert */}
                    {stats?.critical_risks > 0 && (
                        <div style={{
                            marginTop: 'var(--space-md)',
                            padding: 'var(--space-md)',
                            background: 'var(--critical-bg)',
                            border: '1px solid var(--critical-border)',
                            borderRadius: 'var(--radius-md)',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 'var(--space-sm)',
                        }}>
                            <AlertTriangle size={18} color="var(--critical)" />
                            <span style={{ fontSize: '0.85rem', color: 'var(--critical)', fontWeight: 600 }}>
                                {stats.critical_risks} critical risk{stats.critical_risks > 1 ? 's' : ''} require immediate attention
                            </span>
                        </div>
                    )}
                </div>
            </div>

            {/* Recent Repositories */}
            <div className="card">
                <div className="card-header">
                    <h3 className="card-title">📁 Recent Repositories</h3>
                    <button className="btn btn-ghost btn-sm" onClick={() => navigate('/analyze')}>
                        View All <ArrowRight size={14} />
                    </button>
                </div>

                {repos.length > 0 ? (
                    <div className="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Repository</th>
                                    <th>Language</th>
                                    <th>Status</th>
                                    <th>Risks</th>
                                    <th>Files</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {repos.slice(0, 5).map((repo) => (
                                    <tr key={repo.id}>
                                        <td>
                                            <div style={{ fontWeight: 600 }}>{repo.owner}/{repo.name}</div>
                                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{repo.branch}</div>
                                        </td>
                                        <td>
                                            <span style={{
                                                padding: '2px 8px', background: 'var(--bg-elevated)',
                                                borderRadius: 'var(--radius-full)', fontSize: '0.75rem'
                                            }}>
                                                {repo.language || '—'}
                                            </span>
                                        </td>
                                        <td>
                                            <span className={`badge badge-status badge-${repo.status}`}>
                                                {repo.status}
                                            </span>
                                        </td>
                                        <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                                            {repo.risks?.length || 0}
                                        </td>
                                        <td style={{ color: 'var(--text-secondary)' }}>{repo.file_count}</td>
                                        <td>
                                            <button
                                                className="btn btn-ghost btn-sm"
                                                onClick={() => navigate(`/analyze?repo=${repo.id}`)}
                                            >
                                                View
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="empty-state">
                        <div className="empty-icon">📭</div>
                        <h3>No repositories analyzed yet</h3>
                        <p>Start by analyzing a GitHub repository to see reliability insights.</p>
                        <button className="btn btn-primary" style={{ marginTop: 'var(--space-md)' }} onClick={() => navigate('/analyze')}>
                            <Brain size={18} /> Analyze Repository
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
