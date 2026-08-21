import React, { useState } from 'react';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Volume2, 
  User, 
  Sparkles, 
  CheckCircle, 
  FileText, 
  Download,
  Share2,
  Clock,
  ThumbsUp,
  Tag
} from 'lucide-react';
import { MOCK_AUDIO_SESSION } from '../data/mockData';

export const AudioAnalyzer: React.FC = () => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeLineId, setActiveLineId] = useState<number | null>(3);
  const [progress, setProgress] = useState(35);
  const [checkedActions, setCheckedActions] = useState<Record<number, boolean>>({});

  const togglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  const toggleAction = (idx: number) => {
    setCheckedActions(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header Bar */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <span style={{ padding: '4px 10px', background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', borderRadius: '20px', fontSize: '12px', fontWeight: 600 }}>
              AI Call Transcription
            </span>
            <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Recorded on {MOCK_AUDIO_SESSION.date}</span>
          </div>
          <h2 style={{ fontSize: '22px', fontWeight: 800, color: '#ffffff' }}>
            {MOCK_AUDIO_SESSION.title}
          </h2>
          <div style={{ display: 'flex', gap: '16px', marginTop: '8px', fontSize: '14px', color: 'var(--text-secondary)' }}>
            <span><User size={14} style={{ verticalAlign: 'middle', marginRight: '4px' }} /> {MOCK_AUDIO_SESSION.customerName} ({MOCK_AUDIO_SESSION.company})</span>
            <span><Clock size={14} style={{ verticalAlign: 'middle', marginRight: '4px' }} /> {MOCK_AUDIO_SESSION.duration}</span>
            <span><ThumbsUp size={14} style={{ verticalAlign: 'middle', marginRight: '4px', color: '#34d399' }} /> CSAT: {MOCK_AUDIO_SESSION.csatScore}/10</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="button-secondary"><Share2 size={16} /> Share</button>
          <button className="button-primary"><Download size={16} /> Export Takeaways PDF</button>
        </div>
      </div>

      {/* Audio Waveform Player Control */}
      <div className="glass-panel" style={{ padding: '20px 28px', background: 'rgba(15, 23, 42, 0.9)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <button 
            onClick={togglePlay}
            style={{ 
              width: '48px', 
              height: '48px', 
              borderRadius: '50%', 
              background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
              border: 'none',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              boxShadow: '0 4px 15px rgba(99, 102, 241, 0.4)'
            }}
          >
            {isPlaying ? <Pause size={22} /> : <Play size={22} style={{ marginLeft: '2px' }} />}
          </button>

          <button style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <RotateCcw size={18} />
          </button>

          {/* Waveform graphic & Scrubber */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-muted)' }}>
              <span>03:40</span>
              <span>14:32</span>
            </div>
            
            {/* Waveform Bar simulation */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '3px', height: '28px', cursor: 'pointer' }} onClick={(e) => setProgress(Math.floor((e.clientX % 300) / 3))}>
              {Array.from({ length: 55 }).map((_, i) => {
                const height = Math.sin(i * 0.4) * 12 + 16;
                const isPlayed = i / 55 <= progress / 100;
                return (
                  <div 
                    key={i} 
                    style={{ 
                      flex: 1, 
                      height: `${height}px`, 
                      backgroundColor: isPlayed ? '#6366f1' : 'rgba(255, 255, 255, 0.15)',
                      borderRadius: '2px',
                      transition: 'all 0.15s ease'
                    }} 
                  />
                );
              })}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)' }}>
            <Volume2 size={18} />
            <span style={{ fontSize: '12px', fontWeight: 600 }}>1.0x</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Transcript vs AI Takeaways */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        {/* Live Transcript with Sentiment Diarization */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileText size={18} color="#818cf8" /> Interactive Transcript & Speaker Sentiment
            </h3>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Click timestamp to play line</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {MOCK_AUDIO_SESSION.transcripts.map((line) => {
              const isActive = activeLineId === line.id;
              return (
                <div 
                  key={line.id} 
                  onClick={() => setActiveLineId(line.id)}
                  style={{ 
                    padding: '16px', 
                    borderRadius: '12px', 
                    background: isActive ? 'rgba(99, 102, 241, 0.12)' : 'rgba(255, 255, 255, 0.02)',
                    border: isActive ? '1px solid rgba(99, 102, 241, 0.4)' : '1px solid rgba(255, 255, 255, 0.05)',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ 
                        fontWeight: 700, 
                        fontSize: '13px', 
                        color: line.role === 'Customer' ? '#38bdf8' : '#a5b4fc' 
                      }}>
                        {line.speaker}
                      </span>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        [{line.timestamp}]
                      </span>
                    </div>

                    <span className={`badge badge-${line.sentiment}`}>
                      {line.sentiment}
                    </span>
                  </div>

                  <p style={{ fontSize: '14px', color: '#f1f5f9', lineHeight: '1.5', margin: '6px 0' }}>
                    "{line.text}"
                  </p>

                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '10px' }}>
                    {line.keywords.map((kw, i) => (
                      <span key={i} style={{ 
                        fontSize: '11px', 
                        padding: '2px 8px', 
                        borderRadius: '6px', 
                        background: 'rgba(255, 255, 255, 0.06)',
                        color: 'var(--text-secondary)',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}>
                        <Tag size={10} /> {kw}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* AI Key Takeaways & Action Items */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="glass-panel" style={{ 
            padding: '24px', 
            background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%)',
            border: '1px solid rgba(168, 85, 247, 0.25)' 
          }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
              <Sparkles size={18} color="#c084fc" /> AI Extracted Action Items
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {MOCK_AUDIO_SESSION.aiActionItems.map((item, idx) => (
                <div 
                  key={idx} 
                  onClick={() => toggleAction(idx)}
                  style={{ 
                    display: 'flex', 
                    gap: '10px', 
                    alignItems: 'flex-start', 
                    cursor: 'pointer',
                    padding: '8px',
                    borderRadius: '8px',
                    background: checkedActions[idx] ? 'rgba(16, 185, 129, 0.1)' : 'transparent'
                  }}
                >
                  <CheckCircle 
                    size={18} 
                    style={{ 
                      marginTop: '2px', 
                      flexShrink: 0, 
                      color: checkedActions[idx] ? '#34d399' : 'var(--text-muted)' 
                    }} 
                  />
                  <span style={{ 
                    fontSize: '13px', 
                    color: checkedActions[idx] ? 'var(--text-muted)' : '#f8fafc',
                    textDecoration: checkedActions[idx] ? 'line-through' : 'none'
                  }}>
                    {item}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Key Topics Cluster */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#ffffff', marginBottom: '12px' }}>
              Extracted Topics
            </h3>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {MOCK_AUDIO_SESSION.keyTopics.map((topic, i) => (
                <span key={i} style={{ 
                  padding: '6px 12px', 
                  borderRadius: '20px', 
                  background: 'rgba(99, 102, 241, 0.15)', 
                  border: '1px solid rgba(99, 102, 241, 0.3)',
                  color: '#a5b4fc', 
                  fontSize: '12px', 
                  fontWeight: 600 
                }}>
                  {topic}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
