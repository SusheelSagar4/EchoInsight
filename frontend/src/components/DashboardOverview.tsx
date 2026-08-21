import React from 'react';
import { 
  TrendingUp, 
  MessageSquare, 
  Mic, 
  ThumbsUp, 
  AlertTriangle, 
  ArrowUpRight, 
  Sparkles,
  Zap,
  Layers
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell 
} from 'recharts';
import { SENTIMENT_TREND_DATA, MOCK_FEEDBACKS, MOCK_TOPIC_CLUSTERS } from '../data/mockData';

interface DashboardProps {
  onNavigate: (view: 'overview' | 'audio' | 'feedback' | 'topics') => void;
}

export const DashboardOverview: React.FC<DashboardProps> = ({ onNavigate }) => {
  const pieData = [
    { name: 'Positive', value: 76, color: '#10b981' },
    { name: 'Neutral', value: 16, color: '#f59e0b' },
    { name: 'Negative', value: 8, color: '#f43f5e' }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner */}
      <div className="glass-panel" style={{ 
        padding: '24px 32px', 
        background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(6, 182, 212, 0.1) 100%)',
        border: '1px solid rgba(99, 102, 241, 0.25)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <span className="badge badge-positive">
              <span className="pulse-dot"></span> Live AI Stream
            </span>
            <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Updated 2 mins ago</span>
          </div>
          <h1 style={{ fontSize: '26px', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.5px' }}>
            AI Feedback & Call Insights
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '4px' }}>
            Synthesizing customer reviews, sales recordings, and support tickets into actionable product priorities.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="button-secondary" onClick={() => onNavigate('audio')}>
            <Mic size={16} /> Analyze Audio Call
          </button>
          <button className="button-primary" onClick={() => onNavigate('feedback')}>
            <Sparkles size={16} /> Review Feedbacks
          </button>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', 
        gap: '20px' 
      }}>
        <div className="glass-panel glass-panel-hover" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>Overall CSAT Score</span>
            <div style={{ padding: '8px', background: 'rgba(16, 185, 129, 0.12)', borderRadius: '10px', color: '#34d399' }}>
              <ThumbsUp size={18} />
            </div>
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: '#ffffff' }}>88.4%</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px', fontSize: '13px', color: '#34d399' }}>
            <TrendingUp size={14} /> +4.2% from last week
          </div>
        </div>

        <div className="glass-panel glass-panel-hover" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>Net Promoter Score (NPS)</span>
            <div style={{ padding: '8px', background: 'rgba(99, 102, 241, 0.12)', borderRadius: '10px', color: '#818cf8' }}>
              <Zap size={18} />
            </div>
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: '#ffffff' }}>+54</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px', fontSize: '13px', color: '#818cf8' }}>
            <ArrowUpRight size={14} /> Top 10% Industry Tier
          </div>
        </div>

        <div className="glass-panel glass-panel-hover" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>Total Feedbacks Processed</span>
            <div style={{ padding: '8px', background: 'rgba(6, 182, 212, 0.12)', borderRadius: '10px', color: '#38bdf8' }}>
              <MessageSquare size={18} />
            </div>
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: '#ffffff' }}>1,482</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px', fontSize: '13px', color: '#38bdf8' }}>
            <TrendingUp size={14} /> +210 new this week
          </div>
        </div>

        <div className="glass-panel glass-panel-hover" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>Critical Issue Clusters</span>
            <div style={{ padding: '8px', background: 'rgba(244, 63, 94, 0.12)', borderRadius: '10px', color: '#f87171' }}>
              <AlertTriangle size={18} />
            </div>
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: '#ffffff' }}>1 Critical</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px', fontSize: '13px', color: '#f87171' }}>
            Mobile Upload Timeout Bug
          </div>
        </div>
      </div>

      {/* Analytics Charts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        {/* Sentiment Trend Area Chart */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#ffffff' }}>7-Day Sentiment Velocity</h3>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Daily breakdown of positive, neutral, and negative sentiment ratios.</p>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <span className="badge badge-positive">Positive (76%)</span>
              <span className="badge badge-negative">Negative (8%)</span>
            </div>
          </div>

          <div style={{ width: '100%', height: '260px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={SENTIMENT_TREND_DATA}>
                <defs>
                  <linearGradient id="colorPos" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorNeg" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#f43f5e" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="day" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px', color: '#fff' }} 
                />
                <Area type="monotone" dataKey="positive" stroke="#10b981" fillOpacity={1} fill="url(#colorPos)" strokeWidth={2} />
                <Area type="monotone" dataKey="negative" stroke="#f43f5e" fillOpacity={1} fill="url(#colorNeg)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sentiment Distribution Pie */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#ffffff' }}>Sentiment Ratio</h3>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Proportion across all channels.</p>
          </div>

          <div style={{ width: '100%', height: '180px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px', color: '#fff' }} 
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-around', paddingTop: '10px', borderTop: '1px solid var(--border-glass)' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '12px', color: '#34d399', fontWeight: 600 }}>Positive</div>
              <div style={{ fontSize: '16px', fontWeight: 700 }}>76%</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '12px', color: '#fbbf24', fontWeight: 600 }}>Neutral</div>
              <div style={{ fontSize: '16px', fontWeight: 700 }}>16%</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '12px', color: '#f87171', fontWeight: 600 }}>Negative</div>
              <div style={{ fontSize: '16px', fontWeight: 700 }}>8%</div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Grid: Recent Feedbacks & Critical Clusters */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Recent Live Feedbacks */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#ffffff' }}>Latest Feedbacks</h3>
            <button 
              onClick={() => onNavigate('feedback')} 
              style={{ background: 'none', border: 'none', color: '#818cf8', cursor: 'pointer', fontWeight: 600, fontSize: '13px' }}
            >
              View All →
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {MOCK_FEEDBACKS.slice(0, 3).map((item) => (
              <div key={item.id} style={{ 
                padding: '14px', 
                background: 'rgba(255, 255, 255, 0.03)', 
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                display: 'flex',
                gap: '12px',
                alignItems: 'flex-start'
              }}>
                <img 
                  src={item.avatar} 
                  alt={item.author} 
                  style={{ width: '38px', height: '38px', borderRadius: '50%', objectFit: 'cover' }} 
                />
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 600, fontSize: '14px', color: '#f8fafc' }}>{item.author}</span>
                    <span className={`badge badge-${item.sentiment}`}>{item.sentiment}</span>
                  </div>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                    "{item.content}"
                  </p>
                  <div style={{ display: 'flex', gap: '8px', marginTop: '8px', alignItems: 'center' }}>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{item.source} • {item.timestamp}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Topic Clusters */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#ffffff' }}>Top Feature & Pain Point Clusters</h3>
            <button 
              onClick={() => onNavigate('topics')} 
              style={{ background: 'none', border: 'none', color: '#818cf8', cursor: 'pointer', fontWeight: 600, fontSize: '13px' }}
            >
              Explore Clusters →
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {MOCK_TOPIC_CLUSTERS.slice(0, 3).map((cluster) => (
              <div key={cluster.id} style={{ 
                padding: '14px', 
                background: 'rgba(255, 255, 255, 0.03)', 
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 700, fontSize: '14px', color: '#f8fafc' }}>{cluster.name}</span>
                    <span style={{ 
                      fontSize: '11px', 
                      padding: '2px 8px', 
                      borderRadius: '10px',
                      background: cluster.urgency === 'Critical' ? 'rgba(244,63,94,0.2)' : 'rgba(99,102,241,0.2)',
                      color: cluster.urgency === 'Critical' ? '#f87171' : '#a5b4fc'
                    }}>
                      {cluster.urgency}
                    </span>
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                    {cluster.mentionCount} User Mentions • {cluster.growthTrend}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <Layers size={18} style={{ color: 'var(--text-muted)' }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
