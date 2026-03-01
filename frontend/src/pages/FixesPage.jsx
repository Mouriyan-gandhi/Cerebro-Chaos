import React, { useState, useEffect } from 'react';
import { Wrench, Copy, Check, ExternalLink } from 'lucide-react';
import api from '../services/api';

export default function FixesPage() {
    const [repos, setRepos] = useState([]);
    const [selectedRepo, setSelectedRepo] = useState(null);
    const [risks, setRisks] = useState([]);
    const [fixes, setFixes] = useState({});
    const [loading, setLoading] = useState({});
    const [copiedId, setCopiedId] = useState(null);

    useEffect(() => {
        loadRepos();
    }, []);

    async function loadRepos() {
        try {
            const data = await api.listRepos();
            const completed = (data || []).filter(r => r.status === 'completed');
            setRepos(completed);
            if (completed.length > 0) {
                selectRepo(completed[0]);
            }
        } catch (err) {
            console.error(err);
        }
    }

    async function selectRepo(repo) {
        setSelectedRepo(repo);
        try {
            const risksData = await api.getRisks(repo.id);
            setRisks(risksData || []);
        } catch (err) {
            setRisks(repo.risks || []);
        }
    }

    async function loadFix(riskId) {
        if (fixes[riskId]) return;
        setLoading(prev => ({ ...prev, [riskId]: true }));
        try {
            const fix = await api.getFixSuggestion(riskId);
            setFixes(prev => ({ ...prev, [riskId]: fix }));
        } catch (err) {
            console.error('Failed to load fix:', err);
        }
        setLoading(prev => ({ ...prev, [riskId]: false }));
    }

    function copyCode(code, riskId) {
        navigator.clipboard.writeText(code);
        setCopiedId(riskId);
        setTimeout(() => setCopiedId(null), 2000);
    }

    const effortColors = {
        low: 'var(--success)',
        medium: 'var(--warning)',
        high: 'var(--critical)',
    };

    return (
        <div className="fade-in">
            <div className="page-header">
                <h2>🔧 Fix Suggestions</h2>
                <p>AI-generated code fixes for detected reliability risks</p>
            </div>

            {/* Repo Selector */}
            {repos.length > 0 && (
                <div className="card" style={{ marginBottom: 'var(--space-md)' }}>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                        {repos.map(repo => (
                            <button
                                key={repo.id}
                                className={`btn ${selectedRepo?.id === repo.id ? 'btn-primary' : 'btn-ghost'} btn-sm`}
                                onClick={() => selectRepo(repo)}
                            >
                                {repo.owner}/{repo.name}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Fixes */}
            {risks.length > 0 ? (
                <div className="stagger" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
                    {risks.map(risk => {
                        const fix = fixes[risk.id];
                        const isLoading = loading[risk.id];

                        return (
                            <div key={risk.id} className="card fix-card">
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-md)' }}>
                                    <div>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                                            <span className={`badge badge-${risk.severity}`}>{risk.severity}</span>
                                            <span style={{
                                                padding: '2px 8px', background: 'var(--bg-elevated)',
                                                borderRadius: 'var(--radius-full)', fontSize: '0.72rem',
                                                color: 'var(--text-secondary)',
                                            }}>
                                                {risk.category}
                                            </span>
                                        </div>
                                        <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '4px' }}>
                                            {risk.title}
                                        </h4>
                                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                            {risk.description}
                                        </p>
                                        {risk.file_path && (
                                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
                                                📄 {risk.file_path}
                                            </div>
                                        )}
                                    </div>
                                    <div style={{
                                        textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 800,
                                        fontSize: '1.2rem', minWidth: '60px',
                                        color: risk.failure_probability >= 0.7 ? 'var(--critical)' :
                                            risk.failure_probability >= 0.4 ? 'var(--warning)' : 'var(--success)',
                                    }}>
                                        {Math.round((risk.failure_probability || 0) * 100)}%
                                    </div>
                                </div>

                                {/* Fix Suggestion */}
                                {risk.fix_suggestion && (
                                    <div style={{
                                        padding: 'var(--space-md)', background: 'var(--success-bg)',
                                        borderRadius: 'var(--radius-md)', border: '1px solid rgba(16,185,129,0.2)',
                                        marginBottom: 'var(--space-md)',
                                    }}>
                                        <div className="fix-header" style={{ marginBottom: '8px' }}>
                                            <Wrench size={16} color="var(--success)" />
                                            <h4 style={{ color: 'var(--success)' }}>Recommended Fix</h4>
                                        </div>
                                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                            {risk.fix_suggestion}
                                        </p>
                                    </div>
                                )}

                                {/* Fix Code */}
                                {risk.fix_code && (
                                    <div style={{ position: 'relative' }}>
                                        <div style={{
                                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                            marginBottom: '6px',
                                        }}>
                                            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                                                Suggested Code
                                            </span>
                                            <button
                                                className="btn btn-ghost btn-sm"
                                                onClick={() => copyCode(risk.fix_code, risk.id)}
                                            >
                                                {copiedId === risk.id ? (
                                                    <><Check size={14} color="var(--success)" /> Copied!</>
                                                ) : (
                                                    <><Copy size={14} /> Copy</>
                                                )}
                                            </button>
                                        </div>
                                        <div className="code-block">{risk.fix_code}</div>
                                    </div>
                                )}

                                {/* Load detailed fix */}
                                {!risk.fix_code && !fix && (
                                    <button
                                        className="btn btn-ghost btn-sm"
                                        onClick={() => loadFix(risk.id)}
                                        disabled={isLoading}
                                    >
                                        {isLoading ? 'Loading fix...' : '🔍 Generate Detailed Fix'}
                                    </button>
                                )}

                                {fix && (
                                    <div style={{ marginTop: 'var(--space-md)' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                            <span className="fix-effort" style={{ color: effortColors[fix.implementation_effort] }}>
                                                Effort: {fix.implementation_effort}
                                            </span>
                                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                                Confidence: {Math.round((fix.confidence || 0) * 100)}%
                                            </span>
                                        </div>
                                        <p className="fix-description">{fix.description}</p>
                                        {fix.suggested_code && (
                                            <div style={{ position: 'relative' }}>
                                                <button
                                                    className="btn btn-ghost btn-sm"
                                                    style={{ position: 'absolute', top: '8px', right: '8px', zIndex: 10 }}
                                                    onClick={() => copyCode(fix.suggested_code, `fix-${risk.id}`)}
                                                >
                                                    {copiedId === `fix-${risk.id}` ? <Check size={14} /> : <Copy size={14} />}
                                                </button>
                                                <div className="code-block">{fix.suggested_code}</div>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            ) : (
                <div className="card">
                    <div className="empty-state">
                        <div className="empty-icon">🔨</div>
                        <h3>No risks to fix</h3>
                        <p>Analyze a repository first to detect risks and generate fix suggestions.</p>
                    </div>
                </div>
            )}
        </div>
    );
}
