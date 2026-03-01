import React, { useState, useEffect } from 'react';
import { AlertTriangle, Filter } from 'lucide-react';
import api from '../services/api';
import RiskList from '../components/RiskList';

export default function RiskMapPage() {
    const [repos, setRepos] = useState([]);
    const [selectedRepo, setSelectedRepo] = useState(null);
    const [risks, setRisks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all');

    useEffect(() => {
        loadRepos();
    }, []);

    async function loadRepos() {
        try {
            const data = await api.listRepos();
            setRepos(data || []);

            // Auto-select first completed repo
            const completed = (data || []).find(r => r.status === 'completed');
            if (completed) {
                selectRepo(completed);
            }
        } catch (err) {
            console.error('Failed to load repos:', err);
        }
        setLoading(false);
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

    const filteredRisks = filter === 'all'
        ? risks
        : risks.filter(r => r.severity === filter);

    const riskCounts = {
        all: risks.length,
        critical: risks.filter(r => r.severity === 'critical').length,
        high: risks.filter(r => r.severity === 'high').length,
        medium: risks.filter(r => r.severity === 'medium').length,
        low: risks.filter(r => r.severity === 'low').length,
    };

    return (
        <div className="fade-in">
            <div className="page-header">
                <h2>⚠️ Risk Map</h2>
                <p>All detected reliability risks across your repositories</p>
            </div>

            {/* Repo Selector */}
            {repos.length > 1 && (
                <div className="card" style={{ marginBottom: 'var(--space-md)' }}>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                        {repos.filter(r => r.status === 'completed').map(repo => (
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

            {/* Filter Tabs */}
            <div className="tabs">
                {['all', 'critical', 'high', 'medium', 'low'].map(sev => (
                    <button
                        key={sev}
                        className={`tab ${filter === sev ? 'active' : ''}`}
                        onClick={() => setFilter(sev)}
                    >
                        {sev.charAt(0).toUpperCase() + sev.slice(1)}
                        <span style={{
                            marginLeft: '6px', fontFamily: 'var(--font-mono)',
                            fontSize: '0.72rem', opacity: 0.7,
                        }}>
                            ({riskCounts[sev]})
                        </span>
                    </button>
                ))}
            </div>

            {/* Summary Stats */}
            {risks.length > 0 && (
                <div className="stats-grid" style={{ marginBottom: 'var(--space-md)' }}>
                    <div className="card stat-card danger">
                        <div className="stat-value">{riskCounts.critical}</div>
                        <div className="stat-label">Critical</div>
                    </div>
                    <div className="card stat-card warning">
                        <div className="stat-value">{riskCounts.high}</div>
                        <div className="stat-label">High</div>
                    </div>
                    <div className="card stat-card" style={{ position: 'relative' }}>
                        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '3px', background: 'var(--medium)', borderRadius: 'var(--radius-lg) var(--radius-lg) 0 0' }}></div>
                        <div className="stat-value" style={{ color: 'var(--medium)' }}>{riskCounts.medium}</div>
                        <div className="stat-label">Medium</div>
                    </div>
                    <div className="card stat-card success">
                        <div className="stat-value">{riskCounts.low}</div>
                        <div className="stat-label">Low</div>
                    </div>
                </div>
            )}

            {/* Risk List */}
            <RiskList risks={filteredRisks} />
        </div>
    );
}
