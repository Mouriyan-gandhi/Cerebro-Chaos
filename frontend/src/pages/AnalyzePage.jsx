import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { GitBranch, Search, Trash2, ArrowRight } from 'lucide-react';
import api from '../services/api';
import AnalysisProgress from '../components/AnalysisProgress';
import DependencyGraph from '../components/DependencyGraph';
import RiskList from '../components/RiskList';

export default function AnalyzePage() {
    const [searchParams] = useSearchParams();
    const [repoUrl, setRepoUrl] = useState('');
    const [branch, setBranch] = useState('main');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [currentRepo, setCurrentRepo] = useState(null);
    const [graph, setGraph] = useState({ nodes: [], edges: [] });
    const [repos, setRepos] = useState([]);

    useEffect(() => {
        loadRepos();
        const repoId = searchParams.get('repo');
        if (repoId) {
            loadRepo(repoId);
        }
    }, [searchParams]);

    // Polling for status updates
    useEffect(() => {
        if (!currentRepo || ['completed', 'failed'].includes(currentRepo.status)) return;

        const timer = setInterval(async () => {
            try {
                const updated = await api.getRepo(currentRepo.id);
                setCurrentRepo(updated);

                if (updated.status === 'completed') {
                    const graphData = await api.getGraph(updated.id);
                    setGraph(graphData);
                    loadRepos();
                }
            } catch (err) {
                console.error('Polling error:', err);
            }
        }, 2000);

        return () => clearInterval(timer);
    }, [currentRepo?.id, currentRepo?.status]);

    async function loadRepos() {
        try {
            const data = await api.listRepos();
            setRepos(data || []);
        } catch (err) {
            console.error('Failed to load repos:', err);
        }
    }

    async function loadRepo(repoId) {
        try {
            const repo = await api.getRepo(repoId);
            setCurrentRepo(repo);
            if (repo.status === 'completed') {
                const graphData = await api.getGraph(repoId);
                setGraph(graphData);
            }
        } catch (err) {
            setError(err.message);
        }
    }

    async function handleAnalyze(e) {
        e.preventDefault();
        if (!repoUrl.trim()) return;

        setLoading(true);
        setError(null);

        try {
            const repo = await api.analyzeRepo(repoUrl.trim(), branch);
            setCurrentRepo(repo);
            loadRepos();
        } catch (err) {
            setError(err.message);
        }
        setLoading(false);
    }

    async function handleDelete(repoId) {
        try {
            await api.deleteRepo(repoId);
            setRepos(repos.filter(r => r.id !== repoId));
            if (currentRepo?.id === repoId) {
                setCurrentRepo(null);
                setGraph({ nodes: [], edges: [] });
            }
        } catch (err) {
            console.error('Delete failed:', err);
        }
    }

    async function handleSimulate(risk) {
        if (!currentRepo) return;
        try {
            await api.runChaosTest(currentRepo.id, {
                risk_id: risk.id,
                test_type: 'latency',
            });
        } catch (err) {
            console.error('Simulation failed:', err);
        }
    }

    return (
        <div className="fade-in">
            <div className="page-header">
                <h2>🔍 Repository Analysis</h2>
                <p>Enter a GitHub repository URL to analyze its architecture and detect reliability risks.</p>
            </div>

            {/* Input Form */}
            <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
                <form onSubmit={handleAnalyze}>
                    <div className="input-group">
                        <GitBranch size={20} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                        <input
                            type="text"
                            className="input"
                            placeholder="https://github.com/owner/repo"
                            value={repoUrl}
                            onChange={(e) => setRepoUrl(e.target.value)}
                            disabled={loading}
                        />
                        <input
                            type="text"
                            className="input"
                            placeholder="Branch"
                            value={branch}
                            onChange={(e) => setBranch(e.target.value)}
                            style={{ maxWidth: '120px' }}
                            disabled={loading}
                        />
                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={loading || !repoUrl.trim()}
                        >
                            {loading ? (
                                <span className="loading-pulse">Analyzing...</span>
                            ) : (
                                <>
                                    <Search size={16} />
                                    Analyze
                                </>
                            )}
                        </button>
                    </div>
                    {error && (
                        <div style={{
                            marginTop: 'var(--space-sm)',
                            padding: 'var(--space-sm) var(--space-md)',
                            background: 'var(--danger-bg)',
                            border: '1px solid rgba(239,68,68,0.3)',
                            borderRadius: 'var(--radius-sm)',
                            color: 'var(--danger)',
                            fontSize: '0.85rem',
                        }}>
                            {error}
                        </div>
                    )}
                </form>
            </div>

            {/* Analysis Progress */}
            {currentRepo && !['completed', 'failed'].includes(currentRepo.status) && (
                <div style={{ marginBottom: 'var(--space-xl)' }}>
                    <AnalysisProgress status={currentRepo.status} />
                </div>
            )}

            {/* Repository Info */}
            {currentRepo && currentRepo.status === 'completed' && (
                <>
                    <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
                        <div className="card-header">
                            <h3 className="card-title">
                                📦 {currentRepo.owner}/{currentRepo.name}
                            </h3>
                            <span className="badge badge-status badge-completed">completed</span>
                        </div>
                        <div style={{ display: 'flex', gap: 'var(--space-xl)', flexWrap: 'wrap' }}>
                            <div>
                                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600 }}>Language</div>
                                <div style={{ fontWeight: 700, color: 'var(--accent-400)' }}>{currentRepo.language}</div>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600 }}>Files</div>
                                <div style={{ fontWeight: 700 }}>{currentRepo.file_count}</div>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600 }}>Lines</div>
                                <div style={{ fontWeight: 700 }}>{currentRepo.total_lines?.toLocaleString()}</div>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600 }}>Services</div>
                                <div style={{ fontWeight: 700 }}>{currentRepo.services?.length || 0}</div>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600 }}>Risks</div>
                                <div style={{ fontWeight: 700, color: 'var(--critical)' }}>{currentRepo.risks?.length || 0}</div>
                            </div>
                        </div>
                    </div>

                    {/* Dependency Graph */}
                    <div style={{ marginBottom: 'var(--space-xl)' }}>
                        <DependencyGraph nodes={graph.nodes} edges={graph.edges} />
                    </div>

                    {/* Risk List */}
                    <div style={{ marginBottom: 'var(--space-xl)' }}>
                        <RiskList
                            risks={currentRepo.risks || []}
                            onSimulate={handleSimulate}
                        />
                    </div>
                </>
            )}

            {/* Previous Repos */}
            {repos.length > 0 && !currentRepo && (
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">📚 Previously Analyzed</h3>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
                        {repos.map((repo) => (
                            <div key={repo.id} style={{
                                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                padding: 'var(--space-md)', background: 'var(--bg-primary)',
                                borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)',
                            }}>
                                <div>
                                    <div style={{ fontWeight: 600 }}>{repo.owner}/{repo.name}</div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                        {repo.language} · {repo.file_count} files · {repo.risks?.length || 0} risks
                                    </div>
                                </div>
                                <div style={{ display: 'flex', gap: '8px' }}>
                                    <span className={`badge badge-status badge-${repo.status}`}>{repo.status}</span>
                                    <button className="btn btn-ghost btn-sm" onClick={() => loadRepo(repo.id)}>
                                        View <ArrowRight size={14} />
                                    </button>
                                    <button className="btn btn-sm" style={{ color: 'var(--danger)', background: 'var(--danger-bg)' }} onClick={() => handleDelete(repo.id)}>
                                        <Trash2 size={14} />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
