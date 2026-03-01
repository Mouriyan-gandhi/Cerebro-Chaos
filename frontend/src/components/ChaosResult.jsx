import React from 'react';
import { motion } from 'framer-motion';

export default function ChaosResult({ result }) {
    if (!result) return null;

    const latencyIncrease = result.baseline_latency && result.chaos_latency
        ? ((result.chaos_latency - result.baseline_latency) / result.baseline_latency * 100).toFixed(0)
        : 0;

    const errorRatePercent = ((result.error_rate_after || 0) * 100).toFixed(1);
    const failureProb = ((result.failure_probability || 0) * 100).toFixed(0);

    const getMetricClass = (value, thresholds) => {
        if (value >= thresholds[1]) return 'danger';
        if (value >= thresholds[0]) return 'warning';
        return 'good';
    };

    return (
        <motion.div
            className="card scale-in"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
        >
            <div className="card-header">
                <h3 className="card-title">⚡ Chaos Simulation Results</h3>
                <span className={`badge badge-status badge-${result.status || 'completed'}`}>
                    {result.status || 'completed'}
                </span>
            </div>

            {/* Failure Probability Hero */}
            <div style={{
                textAlign: 'center', padding: 'var(--space-lg)',
                marginBottom: 'var(--space-md)',
                background: 'var(--bg-primary)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--border-subtle)',
            }}>
                <div style={{
                    fontSize: '0.72rem', textTransform: 'uppercase',
                    letterSpacing: '0.15em', color: 'var(--text-muted)',
                    fontWeight: 600, marginBottom: 'var(--space-sm)',
                }}>
                    Failure Probability
                </div>
                <div style={{
                    fontSize: '4rem', fontWeight: 900, fontFamily: 'var(--font-mono)',
                    lineHeight: 1,
                    color: failureProb >= 70 ? 'var(--critical)' :
                        failureProb >= 40 ? 'var(--warning)' : 'var(--success)',
                    textShadow: failureProb >= 70
                        ? '0 0 40px rgba(255,51,102,0.4)'
                        : failureProb >= 40
                            ? '0 0 40px rgba(245,158,11,0.3)'
                            : '0 0 40px rgba(16,185,129,0.3)',
                }}>
                    {failureProb}%
                </div>
                <div className="progress-bar" style={{ marginTop: 'var(--space-md)', maxWidth: '300px', margin: 'var(--space-md) auto 0' }}>
                    <div
                        className={`progress-fill ${failureProb >= 70 ? 'critical' : failureProb >= 40 ? 'high' : 'low'}`}
                        style={{ width: `${failureProb}%` }}
                    />
                </div>
            </div>

            {/* Metrics Grid */}
            <div className="chaos-result">
                <div className="chaos-metric">
                    <label>Baseline Latency</label>
                    <div className="metric-value good">
                        {result.baseline_latency?.toFixed(0) || '—'}ms
                    </div>
                </div>
                <div className="chaos-metric">
                    <label>Chaos Latency</label>
                    <div className={`metric-value ${getMetricClass(result.chaos_latency || 0, [500, 2000])}`}>
                        {result.chaos_latency?.toFixed(0) || '—'}ms
                    </div>
                </div>
                <div className="chaos-metric">
                    <label>Latency Increase</label>
                    <div className={`metric-value ${getMetricClass(latencyIncrease, [200, 500])}`}>
                        {latencyIncrease > 0 ? '+' : ''}{latencyIncrease}%
                    </div>
                </div>
                <div className="chaos-metric">
                    <label>Error Rate</label>
                    <div className={`metric-value ${getMetricClass(errorRatePercent, [10, 50])}`}>
                        {errorRatePercent}%
                    </div>
                </div>
            </div>

            {/* Cascading Failures */}
            {result.cascading_failures && result.cascading_failures.length > 0 && (
                <div style={{ marginTop: 'var(--space-md)' }}>
                    <div style={{
                        fontSize: '0.82rem', fontWeight: 600, color: 'var(--critical)',
                        marginBottom: 'var(--space-sm)', display: 'flex', alignItems: 'center', gap: '6px',
                    }}>
                        🔥 Cascading Failures ({result.cascading_failures.length})
                    </div>
                    {result.cascading_failures.map((failure, i) => (
                        <div key={i} style={{
                            padding: 'var(--space-sm) var(--space-md)',
                            background: 'var(--critical-bg)',
                            border: '1px solid var(--critical-border)',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: '0.82rem',
                            color: 'var(--text-secondary)',
                            marginBottom: '4px',
                        }}>
                            {failure}
                        </div>
                    ))}
                </div>
            )}

            {/* Result Summary */}
            {result.result_summary && (
                <div style={{
                    marginTop: 'var(--space-md)',
                    padding: 'var(--space-md)',
                    background: 'var(--bg-primary)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '0.85rem',
                    color: 'var(--text-secondary)',
                    lineHeight: 1.7,
                    whiteSpace: 'pre-line',
                }}>
                    {result.result_summary}
                </div>
            )}
        </motion.div>
    );
}
