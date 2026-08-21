import React from 'react';
import { 
  Layers, 
  Flame, 
  TrendingUp, 
  ArrowRight,
  Zap
} from 'lucide-react';
import { MOCK_TOPIC_CLUSTERS } from '../data/mockData';

export const TopicCluster: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '22px', fontWeight: 800, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={22} color="#6366f1" /> Topic Clusters & Feature Requests
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '4px' }}>
            Automated semantic clustering groups thousands of user comments into distinct product priorities.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <span className="badge badge-positive" style={{ padding: '8px 14px', fontSize: '13px' }}>
            <Zap size={14} /> AI Keyword Model Active
          </span>
        </div>
      </div>

      {/* Cluster Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
        {MOCK_TOPIC_CLUSTERS.map((cluster) => {
          const total = cluster.sentimentBreakdown.positive + cluster.sentimentBreakdown.neutral + cluster.sentimentBreakdown.negative;
          const posPct = Math.round((cluster.sentimentBreakdown.positive / total) * 100);
          const negPct = Math.round((cluster.sentimentBreakdown.negative / total) * 100);

          return (
            <div key={cluster.id} className="glass-panel glass-panel-hover" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <span style={{ 
                    padding: '4px 10px', 
                    borderRadius: '20px', 
                    fontSize: '11px', 
                    fontWeight: 700,
                    background: cluster.urgency === 'Critical' ? 'rgba(244, 63, 94, 0.2)' : 'rgba(99, 102, 241, 0.2)',
                    color: cluster.urgency === 'Critical' ? '#f87171' : '#a5b4fc',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}>
                    {cluster.urgency === 'Critical' && <Flame size={12} />} {cluster.urgency} Urgency
                  </span>

                  <span style={{ fontSize: '12px', color: '#34d399', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                    <TrendingUp size={12} /> {cluster.growthTrend}
                  </span>
                </div>

                <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#ffffff', marginBottom: '8px' }}>
                  {cluster.name}
                </h3>
                
                <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
                  {cluster.mentionCount} total user mentions
                </div>

                {/* Sentiment Distribution Bar */}
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    <span>Sentiment Breakdown</span>
                    <span>{posPct}% Pos / {negPct}% Neg</span>
                  </div>
                  <div style={{ width: '100%', height: '8px', borderRadius: '4px', background: 'rgba(255, 255, 255, 0.1)', overflow: 'hidden', display: 'flex' }}>
                    <div style={{ width: `${posPct}%`, background: '#10b981' }} />
                    <div style={{ width: `${100 - posPct - negPct}%`, background: '#f59e0b' }} />
                    <div style={{ width: `${negPct}%`, background: '#f43f5e' }} />
                  </div>
                </div>

                {/* Sample Quotes */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {cluster.sampleQuotes.map((quote, idx) => (
                    <div key={idx} style={{ 
                      padding: '10px 12px', 
                      borderRadius: '8px', 
                      background: 'rgba(255, 255, 255, 0.03)',
                      borderLeft: '3px solid #6366f1',
                      fontSize: '12px',
                      color: 'var(--text-secondary)',
                      lineHeight: '1.4'
                    }}>
                      "{quote}"
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ marginTop: '20px', paddingTop: '14px', borderTop: '1px solid var(--border-glass)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Auto-tagged from 4 channels</span>
                <button style={{ background: 'none', border: 'none', color: '#818cf8', fontWeight: 600, fontSize: '12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  View All Quotes <ArrowRight size={14} />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
