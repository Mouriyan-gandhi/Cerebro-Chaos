import React, { useEffect, useRef } from 'react';

const SERVICE_COLORS = {
    api: { bg: '#6c3de820', border: '#7c5aff', text: '#b49eff' },
    database: { bg: '#22d3ee20', border: '#22d3ee', text: '#80f8ff' },
    queue: { bg: '#f59e0b20', border: '#f59e0b', text: '#fbbf24' },
    cache: { bg: '#10b98120', border: '#10b981', text: '#34d399' },
    external: { bg: '#ff6b3520', border: '#ff6b35', text: '#ffa07a' },
    gateway: { bg: '#fbbf2420', border: '#fbbf24', text: '#fde68a' },
    internal: { bg: '#6b639420', border: '#6b6394', text: '#a8a3c0' },
    infrastructure: { bg: '#3b82f620', border: '#3b82f6', text: '#93c5fd' },
    unknown: { bg: '#6b639420', border: '#6b6394', text: '#a8a3c0' },
};

const TYPE_ICONS = {
    api: '🌐',
    database: '🗄️',
    queue: '📨',
    cache: '⚡',
    external: '🔗',
    gateway: '🚪',
    internal: '⚙️',
    infrastructure: '🏗️',
    unknown: '📦',
};

export default function DependencyGraph({ nodes = [], edges = [] }) {
    const canvasRef = useRef(null);
    const svgRef = useRef(null);

    useEffect(() => {
        if (!svgRef.current || nodes.length === 0) return;
        drawEdges();
    }, [nodes, edges]);

    if (nodes.length === 0) {
        return (
            <div className="graph-container">
                <div className="card-header">
                    <h3 className="card-title">🔀 Architecture Graph</h3>
                </div>
                <div className="empty-state">
                    <div className="empty-icon">🕸️</div>
                    <h3>No dependency graph yet</h3>
                    <p>Analyze a repository to see its architecture graph</p>
                </div>
            </div>
        );
    }

    // Calculate node positions in a force-directed-like layout
    const positions = calculatePositions(nodes, edges);

    function drawEdges() {
        const svg = svgRef.current;
        svg.innerHTML = '';

        edges.forEach(edge => {
            const from = positions[edge.source];
            const to = positions[edge.target];
            if (!from || !to) return;

            // Draw curved line
            const midX = (from.x + to.x) / 2;
            const midY = (from.y + to.y) / 2 - 30;

            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            const d = `M ${from.x + 60} ${from.y + 18} Q ${midX + 60} ${midY + 18} ${to.x + 60} ${to.y + 18}`;
            path.setAttribute('d', d);
            path.setAttribute('stroke', 'rgba(108, 61, 232, 0.3)');
            path.setAttribute('stroke-width', '2');
            path.setAttribute('fill', 'none');
            path.setAttribute('stroke-dasharray', '6 3');

            // Animated dash
            const animate = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
            animate.setAttribute('attributeName', 'stroke-dashoffset');
            animate.setAttribute('from', '0');
            animate.setAttribute('to', '-18');
            animate.setAttribute('dur', '2s');
            animate.setAttribute('repeatCount', 'indefinite');
            path.appendChild(animate);

            // Arrow marker
            const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
            const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
            marker.setAttribute('id', `arrow-${edge.source}-${edge.target}`);
            marker.setAttribute('markerWidth', '10');
            marker.setAttribute('markerHeight', '7');
            marker.setAttribute('refX', '10');
            marker.setAttribute('refY', '3.5');
            marker.setAttribute('orient', 'auto');
            const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
            polygon.setAttribute('points', '0 0, 10 3.5, 0 7');
            polygon.setAttribute('fill', 'rgba(108, 61, 232, 0.4)');
            marker.appendChild(polygon);
            defs.appendChild(marker);
            svg.appendChild(defs);

            path.setAttribute('marker-end', `url(#arrow-${edge.source}-${edge.target})`);
            svg.appendChild(path);
        });
    }

    return (
        <div className="graph-container">
            <div className="card-header">
                <h3 className="card-title">🔀 Architecture Graph</h3>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {nodes.length} services · {edges.length} connections
                </span>
            </div>
            <div className="graph-canvas" ref={canvasRef}>
                <svg
                    ref={svgRef}
                    style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}
                />
                {nodes.map((node, i) => {
                    const pos = positions[node.id] || { x: 50 + i * 150, y: 100 };
                    const colors = SERVICE_COLORS[node.type] || SERVICE_COLORS.unknown;
                    const icon = TYPE_ICONS[node.type] || '📦';

                    return (
                        <div
                            key={node.id}
                            className={`graph-node ${node.type || ''}`}
                            style={{
                                left: pos.x,
                                top: pos.y,
                                background: colors.bg,
                                borderColor: colors.border,
                                color: colors.text,
                            }}
                        >
                            <span style={{ marginRight: '6px' }}>{icon}</span>
                            {node.label || node.id}
                        </div>
                    );
                })}
            </div>

            {/* Legend */}
            <div style={{
                display: 'flex', gap: '16px', marginTop: 'var(--space-md)',
                flexWrap: 'wrap', justifyContent: 'center'
            }}>
                {Object.entries(SERVICE_COLORS).slice(0, 6).map(([type, colors]) => (
                    <div key={type} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem' }}>
                        <div style={{
                            width: '10px', height: '10px', borderRadius: '50%',
                            background: colors.border
                        }} />
                        <span style={{ color: 'var(--text-muted)', textTransform: 'capitalize' }}>{type}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}

function calculatePositions(nodes, edges) {
    const positions = {};
    const width = 700;
    const height = 350;
    const padding = 20;

    if (nodes.length === 0) return positions;

    // Group nodes by type for better layout
    const groups = {};
    nodes.forEach(node => {
        const type = node.type || 'unknown';
        if (!groups[type]) groups[type] = [];
        groups[type].push(node);
    });

    const groupKeys = Object.keys(groups);
    const cols = Math.ceil(Math.sqrt(nodes.length));
    const rows = Math.ceil(nodes.length / cols);

    let index = 0;
    const cellWidth = (width - padding * 2) / cols;
    const cellHeight = (height - padding * 2) / Math.max(rows, 1);

    nodes.forEach((node, i) => {
        const col = i % cols;
        const row = Math.floor(i / cols);

        positions[node.id] = {
            x: padding + col * cellWidth + (Math.random() * 20 - 10),
            y: padding + row * cellHeight + (Math.random() * 20 - 10),
        };
    });

    return positions;
}
