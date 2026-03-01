import React from 'react';
import { Check, Loader, X, Circle } from 'lucide-react';

const STEPS = [
    { key: 'pending', label: 'Initializing Analysis' },
    { key: 'cloning', label: 'Cloning Repository' },
    { key: 'analyzing', label: 'Analyzing Architecture' },
    { key: 'risk_detection', label: 'Detecting Risks with AI' },
    { key: 'completed', label: 'Analysis Complete' },
];

const STATUS_ORDER = {
    pending: 0, cloning: 1, analyzing: 2, risk_detection: 3, completed: 4, failed: -1,
};

export default function AnalysisProgress({ status = 'pending' }) {
    const currentIndex = STATUS_ORDER[status] ?? 0;
    const isFailed = status === 'failed';

    return (
        <div className="card fade-in">
            <div className="card-header">
                <h3 className="card-title">🔍 Analysis Progress</h3>
                <span className={`badge badge-status badge-${status}`}>
                    {status.replace('_', ' ')}
                </span>
            </div>

            <div className="analysis-steps">
                {STEPS.map((step, index) => {
                    let state = 'pending';
                    if (isFailed && index === currentIndex) state = 'error';
                    else if (index < currentIndex) state = 'done';
                    else if (index === currentIndex) state = 'active';

                    return (
                        <div key={step.key} className={`step ${state}`}>
                            <div className={`step-indicator ${state}`}>
                                {state === 'done' && <Check size={16} />}
                                {state === 'active' && <Loader size={16} className="loading-pulse" />}
                                {state === 'error' && <X size={16} />}
                                {state === 'pending' && <Circle size={12} />}
                            </div>
                            <span className="step-label">{step.label}</span>
                        </div>
                    );
                })}
            </div>

            {status === 'completed' && (
                <div style={{
                    marginTop: 'var(--space-md)',
                    padding: 'var(--space-md)',
                    background: 'var(--success-bg)',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--success)',
                    fontSize: '0.875rem',
                    fontWeight: 500,
                }}>
                    ✅ Analysis completed successfully! Scroll down to see results.
                </div>
            )}

            {isFailed && (
                <div style={{
                    marginTop: 'var(--space-md)',
                    padding: 'var(--space-md)',
                    background: 'var(--danger-bg)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--danger)',
                    fontSize: '0.875rem',
                    fontWeight: 500,
                }}>
                    ❌ Analysis failed. Please check the repository URL and try again.
                </div>
            )}
        </div>
    );
}
