import React, { useState } from 'react';
import { 
  LayoutDashboard, 
  Mic, 
  MessageSquare, 
  Layers, 
  Settings, 
  Sparkles, 
  Bell, 
  Search, 
  ChevronRight
} from 'lucide-react';
import { DashboardOverview } from './components/DashboardOverview';
import { AudioAnalyzer } from './components/AudioAnalyzer';
import { FeedbackHub } from './components/FeedbackHub';
import { TopicCluster } from './components/TopicCluster';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'audio' | 'feedback' | 'topics'>('overview');

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-dark)' }}>
      {/* Sidebar Navigation */}
      <aside style={{ 
        width: '260px', 
        background: 'rgba(11, 15, 25, 0.95)',
        borderRight: '1px solid var(--border-glass)',
        padding: '24px 16px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        flexShrink: 0
      }}>
        <div>
          {/* Logo & Brand */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '0 8px 24px 8px', borderBottom: '1px solid var(--border-glass)' }}>
            <div style={{ 
              width: '40px', 
              height: '40px', 
              borderRadius: '12px', 
              background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              boxShadow: '0 4px 15px rgba(99, 102, 241, 0.4)'
            }}>
              <Sparkles size={22} />
            </div>
            <div>
              <div style={{ fontWeight: 800, fontSize: '18px', letterSpacing: '-0.3px', color: '#ffffff' }}>
                Echo<span style={{ color: '#38bdf8' }}>Insight</span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span className="pulse-dot" style={{ width: '6px', height: '6px' }}></span> AI Engine v2.4
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '20px' }}>
            <button 
              onClick={() => setActiveTab('overview')}
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '12px', 
                padding: '12px 14px', 
                borderRadius: '10px', 
                border: 'none',
                background: activeTab === 'overview' ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                color: activeTab === 'overview' ? '#ffffff' : 'var(--text-secondary)',
                fontWeight: activeTab === 'overview' ? 700 : 500,
                fontSize: '14px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                width: '100%',
                textAlign: 'left'
              }}
            >
              <LayoutDashboard size={18} color={activeTab === 'overview' ? '#818cf8' : '#64748b'} />
              Overview
            </button>

            <button 
              onClick={() => setActiveTab('audio')}
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '12px', 
                padding: '12px 14px', 
                borderRadius: '10px', 
                border: 'none',
                background: activeTab === 'audio' ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                color: activeTab === 'audio' ? '#ffffff' : 'var(--text-secondary)',
                fontWeight: activeTab === 'audio' ? 700 : 500,
                fontSize: '14px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                width: '100%',
                textAlign: 'left'
              }}
            >
              <Mic size={18} color={activeTab === 'audio' ? '#818cf8' : '#64748b'} />
              Call & Audio Analyzer
            </button>

            <button 
              onClick={() => setActiveTab('feedback')}
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '12px', 
                padding: '12px 14px', 
                borderRadius: '10px', 
                border: 'none',
                background: activeTab === 'feedback' ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                color: activeTab === 'feedback' ? '#ffffff' : 'var(--text-secondary)',
                fontWeight: activeTab === 'feedback' ? 700 : 500,
                fontSize: '14px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                width: '100%',
                textAlign: 'left'
              }}
            >
              <MessageSquare size={18} color={activeTab === 'feedback' ? '#818cf8' : '#64748b'} />
              Feedback Feed
            </button>

            <button 
              onClick={() => setActiveTab('topics')}
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '12px', 
                padding: '12px 14px', 
                borderRadius: '10px', 
                border: 'none',
                background: activeTab === 'topics' ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                color: activeTab === 'topics' ? '#ffffff' : 'var(--text-secondary)',
                fontWeight: activeTab === 'topics' ? 700 : 500,
                fontSize: '14px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                width: '100%',
                textAlign: 'left'
              }}
            >
              <Layers size={18} color={activeTab === 'topics' ? '#818cf8' : '#64748b'} />
              Topic Clusters
            </button>
          </nav>
        </div>

        {/* Sidebar Footer User Card */}
        <div style={{ 
          padding: '12px', 
          borderRadius: '12px', 
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid var(--border-glass)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <div style={{ 
            width: '36px', 
            height: '36px', 
            borderRadius: '50%', 
            background: 'linear-gradient(135deg, #a855f7 0%, #6366f1 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 700,
            fontSize: '14px',
            color: '#fff'
          }}>
            SS
          </div>
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <div style={{ fontWeight: 600, fontSize: '13px', color: '#fff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              Susheel Sagar
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Product Lead</div>
          </div>
          <Settings size={16} style={{ color: 'var(--text-muted)', cursor: 'pointer' }} />
        </div>
      </aside>

      {/* Main Content Workspace */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* Header Top Bar */}
        <header style={{ 
          height: '70px', 
          borderBottom: '1px solid var(--border-glass)',
          padding: '0 32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(11, 15, 25, 0.6)',
          backdropFilter: 'blur(12px)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', color: 'var(--text-secondary)' }}>
            <span>EchoInsight</span>
            <ChevronRight size={14} color="#64748b" />
            <span style={{ color: '#ffffff', fontWeight: 600, textTransform: 'capitalize' }}>{activeTab}</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ position: 'relative', width: '240px' }}>
              <Search size={14} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input 
                type="text" 
                placeholder="Global search..." 
                style={{ 
                  width: '100%', 
                  padding: '6px 12px 6px 34px', 
                  borderRadius: '20px', 
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid var(--border-glass)',
                  color: '#fff',
                  fontSize: '12px',
                  outline: 'none'
                }} 
              />
            </div>

            <div style={{ 
              position: 'relative', 
              padding: '8px', 
              borderRadius: '50%', 
              background: 'rgba(255, 255, 255, 0.05)', 
              color: 'var(--text-secondary)',
              cursor: 'pointer' 
            }}>
              <Bell size={16} />
              <span style={{ position: 'absolute', top: '6px', right: '6px', width: '6px', height: '6px', borderRadius: '50%', background: '#f43f5e' }}></span>
            </div>
          </div>
        </header>

        {/* Dynamic Page Views */}
        <div style={{ padding: '32px', flex: 1, overflowY: 'auto' }}>
          {activeTab === 'overview' && <DashboardOverview onNavigate={setActiveTab} />}
          {activeTab === 'audio' && <AudioAnalyzer />}
          {activeTab === 'feedback' && <FeedbackHub />}
          {activeTab === 'topics' && <TopicCluster />}
        </div>
      </main>
    </div>
  );
};

export default App;
