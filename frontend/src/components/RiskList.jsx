import React, { useState } from 'react';
import { AlertTriangle, ChevronRight, FileCode, Zap, Wrench } from 'lucide-react';

export default function RiskList({ risks = [], onSimulate, onViewFix }) {
    const [expandedId, setExpandedId] = useState(null);

    if (risks.length === 0) {
        return (
            <div className="card">
                <div className="card-header">
                    <h3 className="card-title">⚠️ Detected Risks</h3>
                </div>
                <div className="empty-state">
                    <div className="empty-icon">🛡️</div>
                    <h3>No risks detected</h3>
                    <p>Analyze a repository to detect reliability risks</p>
                </div>
            </div>
        );
    }

    const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
    const sortedRisks = [...risks].sort((a, b) =>
        (severityOrder[a.severity] ?? 4) - (severityOrder[b.severity] ?? 4)
    );

    return (
        <div className="card">
            <div className="card-header">
                <h3 className="card-title">⚠️ Detected Risks ({risks.length})</h3>
                <div style={{ display: 'flex', gap: '8px' }}>
                    {['critical', 'high', 'medium', 'low'].map(sev => {
                        const count = risks.filter(r => r.severity === sev).length;
                        return count > 0 ? (
                            <span key={sev} className={`badge badge-${sev}`}>
                                {count} {sev}
                            </span>
                        ) : null;
                    })}
                </div>
            </div>

            <div className="risk-list stagger">
                {sortedRisks.map((risk) => (
                    <div
                        key={risk.id}
                        className="risk-item"
                        onClick={() => setExpandedId(expandedId === risk.id ? null : risk.id)}
                    >
                        <div className={`risk-severity ${risk.severity}`} />

                        <div className="risk-content">
                            <div className="risk-title">{risk.title}</div>
                            <div className="risk-description">{risk.description}</div>

                            <div className="risk-meta">
                                <span className={`badge badge-${risk.severity}`}>
                                    {risk.severity}
                                </span>
                                {risk.category && (
                                    <span style={{
                                        padding: '2px 8px', background: 'var(--bg-elevated)',
                                        borderRadius: 'var(--radius-full)', fontSize: '0.72rem',
                                        color: 'var(--text-secondary)'
                                    }}>
                                        {risk.category}
                                    </span>
                                )}
                                {risk.file_path && (
                                    <span>
                                        <FileCode size={12} />
                                        {risk.file_path}
                                    </span>
                                )}
                            </div>

                            {/* Expanded Content */}
                            {expandedId === risk.id && (
                                <div className="fade-in" style={{ marginTop: 'var(--space-md)' }}>
                                    {risk.code_snippet && (
                                        <div className="code-block" style={{ marginBottom: 'var(--space-md)' }}>
                                            {risk.code_snippet}
                                        </div>
                                    )}

                                    {risk.fix_suggestion && (
                                        <div className="fix-card card" style={{ marginBottom: 'var(--space-md)' }}>
                                            <div className="fix-header">
                                                <Wrench size={16} />
                                                <h4>Suggested Fix</h4>
                                            </div>
                                            <p className="fix-description">{risk.fix_suggestion}</p>
                                            {risk.fix_code && (
                                                <div className="code-block">{risk.fix_code}</div>
                                            )}
                                        </div>
                                    )}

                                    <div style={{ display: 'flex', gap: '8px', marginTop: 'var(--space-sm)' }}>
                                        {onSimulate && (
                                            <button
                                                className="btn btn-accent btn-sm"
                                                onClick={(e) => { e.stopPropagation(); onSimulate(risk); }}
                                            >
                                                <Zap size={14} />
                                                Simulate Failure
                                            </button>
                                        )}
                                        {onViewFix && (
                                            <button
                                                className="btn btn-ghost btn-sm"
                                                onClick={(e) => { e.stopPropagation(); onViewFix(risk); }}
                                            >
                                                <Wrench size={14} />
                                                View Fix
                                            </button>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="risk-probability" style={{
                            color: risk.failure_probability >= 0.7 ? 'var(--critical)' :
                                risk.failure_probability >= 0.5 ? 'var(--warning)' : 'var(--success)'
                        }}>
                            {Math.round((risk.failure_probability || 0) * 100)}%
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
