import React, { useState } from 'react';
import { 
  Search, 
  Plus, 
  Star, 
  AlertCircle, 
  X, 
  Send,
  Sparkles
} from 'lucide-react';
import { MOCK_FEEDBACKS, FeedbackItem } from '../data/mockData';

export const FeedbackHub: React.FC = () => {
  const [feedbacks, setFeedbacks] = useState<FeedbackItem[]>(MOCK_FEEDBACKS);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState<'all' | 'positive' | 'neutral' | 'negative' | 'high_urgency'>('all');
  const [isModalOpen, setIsModalOpen] = useState(false);

  // New feedback form state
  const [newAuthor, setNewAuthor] = useState('');
  const [newSource, setNewSource] = useState<'App Store' | 'Play Store' | 'Intercom' | 'Zendesk' | 'Email' | 'User Interview'>('Intercom');
  const [newContent, setNewContent] = useState('');
  const [newSentiment, setNewSentiment] = useState<'positive' | 'neutral' | 'negative'>('positive');
  const newRating = 5;

  const filteredFeedbacks = feedbacks.filter(item => {
    const matchesSearch = item.content.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          item.author.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          item.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()));

    if (!matchesSearch) return false;

    if (activeFilter === 'positive') return item.sentiment === 'positive';
    if (activeFilter === 'neutral') return item.sentiment === 'neutral';
    if (activeFilter === 'negative') return item.sentiment === 'negative';
    if (activeFilter === 'high_urgency') return item.urgency === 'High';
    return true;
  });

  const handleAddFeedback = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newContent || !newAuthor) return;

    const newItem: FeedbackItem = {
      id: `fb-${Date.now()}`,
      author: newAuthor,
      avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150',
      source: newSource,
      rating: newRating,
      sentiment: newSentiment,
      category: 'Feature Request',
      content: newContent,
      timestamp: 'Just now',
      urgency: newSentiment === 'negative' ? 'High' : 'Low',
      aiSummary: `User submitted feedback via ${newSource}.`,
      tags: ['New Submission', newSource]
    };

    setFeedbacks([newItem, ...feedbacks]);
    setIsModalOpen(false);
    setNewAuthor('');
    setNewContent('');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Search & Filter Header Bar */}
      <div className="glass-panel" style={{ padding: '20px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: '280px' }}>
          <div style={{ position: 'relative', width: '100%' }}>
            <Search size={18} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input 
              type="text" 
              placeholder="Search by keywords, user, tag, or content..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ 
                width: '100%',
                padding: '10px 14px 10px 42px',
                borderRadius: '10px',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid var(--border-glass)',
                color: '#ffffff',
                fontSize: '14px',
                outline: 'none'
              }}
            />
          </div>
        </div>

        {/* Filter Pills */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button 
            onClick={() => setActiveFilter('all')} 
            className="button-secondary"
            style={{ 
              background: activeFilter === 'all' ? 'rgba(99, 102, 241, 0.25)' : 'rgba(255, 255, 255, 0.05)',
              borderColor: activeFilter === 'all' ? '#6366f1' : 'var(--border-glass)'
            }}
          >
            All ({feedbacks.length})
          </button>
          <button 
            onClick={() => setActiveFilter('positive')} 
            className="button-secondary"
            style={{ 
              background: activeFilter === 'positive' ? 'rgba(16, 185, 129, 0.25)' : 'rgba(255, 255, 255, 0.05)',
              color: activeFilter === 'positive' ? '#34d399' : 'var(--text-primary)'
            }}
          >
            Positive
          </button>
          <button 
            onClick={() => setActiveFilter('negative')} 
            className="button-secondary"
            style={{ 
              background: activeFilter === 'negative' ? 'rgba(244, 63, 94, 0.25)' : 'rgba(255, 255, 255, 0.05)',
              color: activeFilter === 'negative' ? '#f87171' : 'var(--text-primary)'
            }}
          >
            Negative
          </button>
          <button 
            onClick={() => setActiveFilter('high_urgency')} 
            className="button-secondary"
            style={{ 
              background: activeFilter === 'high_urgency' ? 'rgba(245, 158, 11, 0.25)' : 'rgba(255, 255, 255, 0.05)',
              color: activeFilter === 'high_urgency' ? '#fbbf24' : 'var(--text-primary)'
            }}
          >
            High Urgency
          </button>
        </div>

        <button className="button-primary" onClick={() => setIsModalOpen(true)}>
          <Plus size={16} /> Log Feedback
        </button>
      </div>

      {/* Feedback Feed Cards List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {filteredFeedbacks.length === 0 ? (
          <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No feedbacks match your active search query or filter.
          </div>
        ) : (
          filteredFeedbacks.map((item) => (
            <div key={item.id} className="glass-panel glass-panel-hover" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <img 
                    src={item.avatar} 
                    alt={item.author} 
                    style={{ width: '44px', height: '44px', borderRadius: '50%', objectFit: 'cover' }} 
                  />
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: 700, fontSize: '16px', color: '#ffffff' }}>{item.author}</span>
                      <span style={{ fontSize: '12px', padding: '2px 8px', borderRadius: '12px', background: 'rgba(255, 255, 255, 0.08)', color: 'var(--text-muted)' }}>
                        {item.source}
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '4px' }}>
                      {Array.from({ length: 5 }).map((_, i) => (
                        <Star key={i} size={14} fill={i < item.rating ? '#f59e0b' : 'none'} color={i < item.rating ? '#f59e0b' : '#64748b'} />
                      ))}
                      <span style={{ fontSize: '12px', color: 'var(--text-muted)', marginLeft: '6px' }}>{item.timestamp}</span>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className={`badge badge-${item.sentiment}`}>{item.sentiment}</span>
                  {item.urgency === 'High' && (
                    <span style={{ fontSize: '12px', padding: '4px 10px', borderRadius: '20px', background: 'rgba(244, 63, 94, 0.2)', color: '#f87171', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      <AlertCircle size={12} /> High Priority
                    </span>
                  )}
                </div>
              </div>

              {/* Main Content */}
              <p style={{ fontSize: '15px', color: '#f1f5f9', lineHeight: '1.6', margin: '16px 0' }}>
                "{item.content}"
              </p>

              {/* AI Insight Pill */}
              <div style={{ 
                padding: '12px 16px', 
                borderRadius: '10px', 
                background: 'rgba(99, 102, 241, 0.08)',
                border: '1px solid rgba(99, 102, 241, 0.15)',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                marginBottom: '14px'
              }}>
                <Sparkles size={16} color="#818cf8" style={{ flexShrink: 0 }} />
                <span style={{ fontSize: '13px', color: '#c7d2fe' }}>
                  <strong>AI Summary:</strong> {item.aiSummary}
                </span>
              </div>

              {/* Tags Row */}
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {item.tags.map((tag, idx) => (
                  <span key={idx} style={{ fontSize: '12px', padding: '3px 10px', borderRadius: '6px', background: 'rgba(255, 255, 255, 0.04)', color: 'var(--text-secondary)' }}>
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Log Feedback Modal */}
      {isModalOpen && (
        <div style={{ 
          position: 'fixed', 
          inset: 0, 
          background: 'rgba(0, 0, 0, 0.75)', 
          backdropFilter: 'blur(8px)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 100
        }}>
          <div className="glass-panel" style={{ width: '90%', maxWidth: '520px', padding: '32px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ fontSize: '20px', fontWeight: 800, color: '#ffffff' }}>Log Customer Feedback</h3>
              <button onClick={() => setIsModalOpen(false)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleAddFeedback} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ fontSize: '13px', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>Author Name</label>
                <input 
                  type="text" 
                  required
                  placeholder="e.g. Alex Rivera"
                  value={newAuthor}
                  onChange={(e) => setNewAuthor(e.target.value)}
                  style={{ width: '100%', padding: '10px', borderRadius: '8px', background: 'rgba(255, 255, 255, 0.05)', border: '1px solid var(--border-glass)', color: '#fff' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '13px', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>Channel Source</label>
                  <select 
                    value={newSource}
                    onChange={(e: any) => setNewSource(e.target.value)}
                    style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#1e293b', border: '1px solid var(--border-glass)', color: '#fff' }}
                  >
                    <option value="Intercom">Intercom</option>
                    <option value="App Store">App Store</option>
                    <option value="Play Store">Play Store</option>
                    <option value="Zendesk">Zendesk</option>
                    <option value="Email">Email</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '13px', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>Sentiment</label>
                  <select 
                    value={newSentiment}
                    onChange={(e: any) => setNewSentiment(e.target.value)}
                    style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#1e293b', border: '1px solid var(--border-glass)', color: '#fff' }}
                  >
                    <option value="positive">Positive</option>
                    <option value="neutral">Neutral</option>
                    <option value="negative">Negative</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={{ fontSize: '13px', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>Feedback Content</label>
                <textarea 
                  required
                  rows={4}
                  placeholder="Paste user message or review snippet here..."
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  style={{ width: '100%', padding: '10px', borderRadius: '8px', background: 'rgba(255, 255, 255, 0.05)', border: '1px solid var(--border-glass)', color: '#fff', resize: 'none' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '10px' }}>
                <button type="button" className="button-secondary" onClick={() => setIsModalOpen(false)}>Cancel</button>
                <button type="submit" className="button-primary"><Send size={16} /> Submit Feedback</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
