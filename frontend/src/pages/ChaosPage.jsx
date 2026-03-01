import React, { useState, useEffect } from 'react';
import { Zap, Play, RotateCcw } from 'lucide-react';
import api from '../services/api';
import ChaosResult from '../components/ChaosResult';

const TEST_TYPES = [
    { id: 'latency', name: 'Latency Injection', icon: '⏱️', description: 'Simulate increased response times' },
    { id: 'failure', name: 'Service Failure', icon: '💥', description: 'Simulate complete service crash' },
    { id: 'network', name: 'Network Partition', icon: '🌐', description: 'Simulate network connectivity issues' },
    { id: 'database', name: 'Database Failure', icon: '🗄️', description: 'Simulate database unavailability' },
    { id: 'resource', name: 'Resource Exhaustion', icon: '🔥', description: 'Simulate CPU/memory overload' },
];

export default function ChaosPage() {
    const [repos, setRepos] = useState([]);
    const [selectedRepo, setSelectedRepo] = useState(null);
    const [selectedRisk, setSelectedRisk] = useState(null);
    const [selectedType, setSelectedType] = useState('latency');
    const [running, setRunning] = useState(false);
    const [result, setResult] = useState(null);
    const [history, setHistory] = useState([]);

    useEffect(() => {
        loadRepos();
    }, []);

    async function loadRepos() {
        try {
            const data = await api.listRepos();
            setRepos((data || []).filter(r => r.status === 'completed'));

            const completed = (data || []).find(r => r.status === 'completed');
            if (completed) {
                setSelectedRepo(completed);
                loadHistory(completed.id);
            }
        } catch (err) {
            console.error(err);
        }
    }

    async function loadHistory(repoId) {
        try {
            const tests = await api.listChaosTests(repoId);
            setHistory(tests || []);
        } catch (err) {
            console.error(err);
        }
    }

    async function runTest() {
        if (!selectedRepo) return;
        setRunning(true);
        setResult(null);

        try {
            const testData = {
                test_type: selectedType,
                risk_id: selectedRisk?.id || null,
                target_service: selectedRisk?.file_path || null,
                config: {},
            };

            const res = await api.runChaosTest(selectedRepo.id, testData);
            setResult(res);
            loadHistory(selectedRepo.id);
        } catch (err) {
            console.error('Chaos test failed:', err);
        }

        setRunning(false);
    }

    return (
        <div className="fade-in">
            <div className="page-header">
                <h2>⚡ Chaos Simulation</h2>
                <p>Simulate real-world failures to test your system's resilience</p>
            </div>

            <div className="grid-2" style={{ marginBottom: 'var(--space-xl)' }}>
                {/* Configuration Panel */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">🎮 Test Configuration</h3>
                    </div>

                    {/* Repo Selection */}
                    <div style={{ marginBottom: 'var(--space-md)' }}>
                        <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
                            Repository
                        </label>
                        <select
                            className="input"
                            style={{ fontFamily: 'var(--font-sans)' }}
                            value={selectedRepo?.id || ''}
                            onChange={(e) => {
                                const repo = repos.find(r => r.id === e.target.value);
                                setSelectedRepo(repo);
                                setSelectedRisk(null);
                                if (repo) loadHistory(repo.id);
                            }}
                        >
                            <option value="">Select repository...</option>
                            {repos.map(repo => (
                                <option key={repo.id} value={repo.id}>
                                    {repo.owner}/{repo.name}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Risk Selection */}
                    {selectedRepo?.risks?.length > 0 && (
                        <div style={{ marginBottom: 'var(--space-md)' }}>
                            <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
                                Target Risk (optional)
                            </label>
                            <select
                                className="input"
                                style={{ fontFamily: 'var(--font-sans)' }}
                                value={selectedRisk?.id || ''}
                                onChange={(e) => {
                                    const risk = selectedRepo.risks.find(r => r.id === e.target.value);
                                    setSelectedRisk(risk || null);
                                }}
                            >
                                <option value="">All services (random)</option>
                                {selectedRepo.risks.map(risk => (
                                    <option key={risk.id} value={risk.id}>
                                        [{risk.severity}] {risk.title}
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}

                    {/* Test Type */}
                    <div style={{ marginBottom: 'var(--space-lg)' }}>
                        <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
                            Simulation Type
                        </label>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            {TEST_TYPES.map(type => (
                                <button
                                    key={type.id}
                                    onClick={() => setSelectedType(type.id)}
                                    style={{
                                        display: 'flex', alignItems: 'center', gap: 'var(--space-sm)',
                                        padding: 'var(--space-sm) var(--space-md)',
                                        background: selectedType === type.id ? 'rgba(108,61,232,0.15)' : 'var(--bg-primary)',
                                        border: `1px solid ${selectedType === type.id ? 'var(--primary-500)' : 'var(--border-subtle)'}`,
                                        borderRadius: 'var(--radius-md)',
                                        cursor: 'pointer',
                                        color: selectedType === type.id ? 'var(--accent-400)' : 'var(--text-secondary)',
                                        fontFamily: 'var(--font-sans)', fontSize: '0.85rem',
                                        transition: 'all var(--transition-fast)',
                                    }}
                                >
                                    <span>{type.icon}</span>
                                    <div style={{ textAlign: 'left' }}>
                                        <div style={{ fontWeight: 600 }}>{type.name}</div>
                                        <div style={{ fontSize: '0.72rem', opacity: 0.7 }}>{type.description}</div>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Run Button */}
                    <button
                        className="btn btn-accent btn-lg"
                        style={{ width: '100%', justifyContent: 'center' }}
                        onClick={runTest}
                        disabled={running || !selectedRepo}
                    >
                        {running ? (
                            <>
                                <span className="loading-spinner" style={{ width: '18px', height: '18px', borderWidth: '2px' }} />
                                Running Simulation...
                            </>
                        ) : (
                            <>
                                <Play size={18} />
                                Run Chaos Simulation
                            </>
                        )}
                    </button>
                </div>

                {/* Results Panel */}
                <div>
                    {result ? (
                        <ChaosResult result={result} />
                    ) : (
                        <div className="card">
                            <div className="empty-state">
                                <div className="empty-icon">🧪</div>
                                <h3>Ready to Simulate</h3>
                                <p>Configure your chaos test and click Run to see what happens when things go wrong.</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Test History */}
            {history.length > 0 && (
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">📜 Test History</h3>
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                            {history.length} test{history.length !== 1 ? 's' : ''}
                        </span>
                    </div>
                    <div className="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Type</th>
                                    <th>Target</th>
                                    <th>Status</th>
                                    <th>Latency</th>
                                    <th>Error Rate</th>
                                    <th>Failure %</th>
                                    <th>Date</th>
                                </tr>
                            </thead>
                            <tbody>
                                {history.map(test => (
                                    <tr key={test.id} onClick={() => setResult(test)} style={{ cursor: 'pointer' }}>
                                        <td style={{ fontWeight: 600 }}>
                                            {TEST_TYPES.find(t => t.id === test.test_type)?.icon || '🧪'}{' '}
                                            {TEST_TYPES.find(t => t.id === test.test_type)?.name || test.test_type}
                                        </td>
                                        <td style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                                            {test.target_service || '—'}
                                        </td>
                                        <td>
                                            <span className={`badge badge-status badge-${test.status}`}>{test.status}</span>
                                        </td>
                                        <td style={{ fontFamily: 'var(--font-mono)' }}>
                                            {test.baseline_latency?.toFixed(0)}ms → {test.chaos_latency?.toFixed(0)}ms
                                        </td>
                                        <td style={{
                                            fontFamily: 'var(--font-mono)', fontWeight: 700,
                                            color: (test.error_rate_after || 0) > 0.5 ? 'var(--critical)' :
                                                (test.error_rate_after || 0) > 0.2 ? 'var(--warning)' : 'var(--success)',
                                        }}>
                                            {((test.error_rate_after || 0) * 100).toFixed(1)}%
                                        </td>
                                        <td style={{
                                            fontFamily: 'var(--font-mono)', fontWeight: 700,
                                            color: (test.failure_probability || 0) > 0.7 ? 'var(--critical)' :
                                                (test.failure_probability || 0) > 0.4 ? 'var(--warning)' : 'var(--success)',
                                        }}>
                                            {((test.failure_probability || 0) * 100).toFixed(0)}%
                                        </td>
                                        <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                            {test.created_at ? new Date(test.created_at).toLocaleDateString() : '—'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}
