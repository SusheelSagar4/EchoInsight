import { useState, useEffect, useRef } from 'react'
import './App.css'

// Base URL for backend API requests, loaded from environment variables (sanitized to remove trailing slashes) or defaulting to live Render backend
const RAW_API_URL = import.meta.env.VITE_API_URL || 'https://echoinsight.onrender.com'
const API_BASE_URL = RAW_API_URL.replace(/\/+$/, '')

// Sample text for the automated landing page typewriter demo
const FULL_DEMO_TEXT = `Users are asking for dark mode support\nThe export button crashes when exporting large reports\nNeed easier user onboarding steps`

// Mock dataset for the automated landing page demo
const DEMO_CLUSTERS_DATA = [
  {
    theme_name: 'Export Performance & Reliability',
    rice_score: 92.5,
    frequency: 14,
    affected_count: 38,
    negative_feedback_count: 12,
    feedback_items: [
      {
        text: 'The export button crashes when exporting large reports',
        sentiment: 'Negative',
        intent: 'Bug Report',
        urgency: 'High',
        similar_past_count: 5,
      },
      {
        text: 'PDF export times out after 30 seconds for big accounts',
        sentiment: 'Negative',
        intent: 'Performance Issue',
        urgency: 'High',
        similar_past_count: 3,
      },
    ],
  },
  {
    theme_name: 'Dark Mode & Visual Ergonomics',
    rice_score: 78.0,
    frequency: 22,
    affected_count: 65,
    negative_feedback_count: 0,
    feedback_items: [
      {
        text: 'Users are asking for dark mode support',
        sentiment: 'Neutral',
        intent: 'Feature Request',
        urgency: 'Medium',
        similar_past_count: 8,
      },
      {
        text: 'The bright white theme strains eyes during late night review sessions',
        sentiment: 'Neutral',
        intent: 'UX Improvement',
        urgency: 'Low',
        similar_past_count: 4,
      },
    ],
  },
]

const DEMO_PRD_DATA = {
  title: 'PRD: High-Scale Report Export Reliability & Async Queue',
  problem_statement:
    'Enterprise customers experience browser crashes and 504 gateway timeouts when exporting reports containing over 10,000 feedback entries. This blocks quarterly product review workflows and creates high support ticket volume.',
  user_stories: [
    'As a Product Manager, I want export jobs to run asynchronously in the background so my browser window never freezes.',
    'As a user, I want a download notification or email link when my large report export completes.',
  ],
  acceptance_criteria: [
    'Export jobs exceeding 1,000 rows automatically enqueue as background tasks.',
    'User receives a progress bar and browser toast notification upon completion.',
    'System handles exports up to 100,000 rows within 5 seconds server-side.',
  ],
  kpis: [
    'Zero browser crash events during report exports.',
    '95% reduction in export-related support tickets.',
    'Average export generation latency < 3 seconds.',
  ],
}

function App() {
  // Navigation mode: 'landing' (default landing page) or 'workspace' (working cluster model)
  const [viewMode, setViewMode] = useState('landing')

  // Working Workspace State
  const [rawFeedback, setRawFeedback] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [clusters, setClusters] = useState([])
  const [generatedPRDs, setGeneratedPRDs] = useState({})
  const [loadingPRDFor, setLoadingPRDFor] = useState(null)
  const [uploadedFile, setUploadedFile] = useState(null)
  const [copiedPRDFor, setCopiedPRDFor] = useState(null)

  // Landing Page One-Shot Demo State (Plays once on scroll and remains permanently visible)
  const [demoText, setDemoText] = useState('')
  const [demoState, setDemoState] = useState('idle') // 'idle', 'typing', 'moving_cursor', 'clicking', 'clustering', 'done'
  const [demoClusters, setDemoClusters] = useState([])
  const [demoPRD, setDemoPRD] = useState(null)
  const [demoCopied, setDemoCopied] = useState(false)

  // Refs for hero section and particle canvas
  const heroRef = useRef(null)
  const canvasRef = useRef(null)

  // Switch helper handlers
  const switchToWorkspace = () => {
    setViewMode('workspace')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const switchToLanding = () => {
    setViewMode('landing')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // Core Demo Runner Function
  const runDemoSequence = useRef(null)
  runDemoSequence.current = () => {
    if (demoState !== 'idle') return

    setDemoState('typing')
    setDemoText('')
    setDemoClusters([])
    setDemoPRD(null)

    let charIndex = 0
    const typewriterTimer = setInterval(() => {
      charIndex++
      setDemoText(FULL_DEMO_TEXT.slice(0, charIndex))

      if (charIndex >= FULL_DEMO_TEXT.length) {
        clearInterval(typewriterTimer)

        // Step 2: Animate cursor moving to button
        setTimeout(() => {
          setDemoState('moving_cursor')

          // Step 3: Trigger click action
          setTimeout(() => {
            setDemoState('clicking')

            // Step 4: Show clustering loader
            setTimeout(() => {
              setDemoState('clustering')

              setTimeout(() => {
                setDemoClusters(DEMO_CLUSTERS_DATA)
                setDemoPRD(DEMO_PRD_DATA)
                setDemoState('done') // Stays permanently visible on screen!
              }, 1000)
            }, 300)
          }, 600)
        }, 400)
      }
    }, 30)
  }

  // Scroll Helper with forced demo trigger
  const scrollToDemo = () => {
    document.getElementById('demo-section')?.scrollIntoView({ behavior: 'smooth' })
    if (demoState === 'idle') {
      setTimeout(() => {
        runDemoSequence.current?.()
      }, 300)
    }
  }

  // One-Shot Scroll Triggered Demo Effect
  useEffect(() => {
    if (viewMode !== 'landing') return

    const demoSection = document.getElementById('demo-section')
    if (!demoSection) return

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries
        if (entry.isIntersecting && demoState === 'idle') {
          runDemoSequence.current?.()
        }
      },
      { threshold: 0.05 }
    )

    observer.observe(demoSection)

    // Fallback scroll listener to guarantee trigger on any scroll
    const handleScrollTrigger = () => {
      if (demoState === 'idle') {
        const rect = demoSection.getBoundingClientRect()
        if (rect.top < window.innerHeight * 0.88) {
          runDemoSequence.current?.()
        }
      }
    }

    window.addEventListener('scroll', handleScrollTrigger, { passive: true })
    handleScrollTrigger()

    return () => {
      window.removeEventListener('scroll', handleScrollTrigger)
      observer.disconnect()
    }
  }, [viewMode, demoState])

  // Hero Particle Canvas System
  useEffect(() => {
    if (viewMode !== 'landing') return

    const canvas = canvasRef.current
    const hero = heroRef.current
    if (!canvas || !hero) return

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (prefersReducedMotion) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animationFrameId = null
    let isHeroVisible = true

    const updateCanvasSize = () => {
      canvas.width = hero.offsetWidth
      canvas.height = hero.offsetHeight
    }
    updateCanvasSize()

    const particleCount = 280
    const particles = []

    for (let i = 0; i < particleCount; i++) {
      const baseVx = (Math.random() - 0.5) * 1.2
      const baseVy = (Math.random() - 0.5) * 1.2
      particles.push({
        x: Math.random() * (canvas.width || 1),
        y: Math.random() * (canvas.height || 1),
        baseVx,
        baseVy,
        vx: baseVx,
        vy: baseVy,
        radius: Math.random() * 2.2 + 1,
        opacity: Math.random() * 0.5 + 0.25,
      })
    }

    const mouse = { x: -9999, y: -9999, isOver: false }

    const handleMouseMove = (e) => {
      const rect = hero.getBoundingClientRect()
      mouse.x = e.clientX - rect.left
      mouse.y = e.clientY - rect.top
      mouse.isOver = true
    }

    const handleMouseLeave = () => {
      mouse.isOver = false
      mouse.x = -9999
      mouse.y = -9999
    }

    const handleResize = () => {
      updateCanvasSize()
    }

    hero.addEventListener('mousemove', handleMouseMove)
    hero.addEventListener('mouseleave', handleMouseLeave)
    window.addEventListener('resize', handleResize)

    const heroObserver = new IntersectionObserver(
      (entries) => {
        const [entry] = entries
        isHeroVisible = entry.isIntersecting
        if (isHeroVisible && !animationFrameId) {
          render()
        }
      },
      { threshold: 0 }
    )

    heroObserver.observe(hero)

    const render = () => {
      if (!isHeroVisible) {
        animationFrameId = null
        return
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height)

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i]

        if (mouse.isOver) {
          const dx = p.x - mouse.x
          const dy = p.y - mouse.y
          const dist = Math.sqrt(dx * dx + dy * dy)
          const repulsionRadius = 180

          if (dist < repulsionRadius && dist > 0) {
            const forceFactor = 1 - dist / repulsionRadius
            const force = forceFactor * forceFactor * 9.0
            const angle = Math.atan2(dy, dx)
            p.vx += Math.cos(angle) * force * 0.35
            p.vy += Math.sin(angle) * force * 0.35
          }
        }

        const currentSpeed = Math.sqrt(p.vx * p.vx + p.vy * p.vy)
        const maxSpeed = 8.5
        if (currentSpeed > maxSpeed) {
          p.vx = (p.vx / currentSpeed) * maxSpeed
          p.vy = (p.vy / currentSpeed) * maxSpeed
        }

        p.vx += (p.baseVx - p.vx) * 0.06
        p.vy += (p.baseVy - p.vy) * 0.06

        p.x += p.vx
        p.y += p.vy

        if (p.x < 0) p.x = canvas.width
        if (p.x > canvas.width) p.x = 0
        if (p.y < 0) p.y = canvas.height
        if (p.y > canvas.height) p.y = 0

        ctx.beginPath()
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(255, 255, 255, ${p.opacity})`
        ctx.fill()
      }

      animationFrameId = requestAnimationFrame(render)
    }

    render()

    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId)
      }
      hero.removeEventListener('mousemove', handleMouseMove)
      hero.removeEventListener('mouseleave', handleMouseLeave)
      window.removeEventListener('resize', handleResize)
      heroObserver.disconnect()
    }
  }, [viewMode])

  // Scroll reveal observer
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible')
          }
        })
      },
      { threshold: 0.08 }
    )

    const elements = document.querySelectorAll('.scroll-reveal')
    elements.forEach((el) => observer.observe(el))

    return () => observer.disconnect()
  }, [clusters, generatedPRDs, viewMode, demoClusters])

  // Working Workspace API Handlers
  const formatPRDAsMarkdown = (prd) => {
    const userStories = (prd.user_stories || []).map((story) => `- ${story}`).join('\n')
    const acceptanceCriteria = (prd.acceptance_criteria || []).map((criterion) => `- ${criterion}`).join('\n')
    const kpis = (prd.kpis || []).map((kpi) => `- ${kpi}`).join('\n')

    return `# ${prd.title || ''}\n\n## Problem Statement\n\n${prd.problem_statement || ''}\n\n## User Stories\n\n${userStories}\n\n## Acceptance Criteria\n\n${acceptanceCriteria}\n\n## KPIs\n\n${kpis}`
  }

  const handleCopyMarkdown = async (cluster, prd) => {
    try {
      const markdownText = formatPRDAsMarkdown(prd)
      await navigator.clipboard.writeText(markdownText)
      setCopiedPRDFor(cluster.theme_name)
      setTimeout(() => setCopiedPRDFor(null), 2000)
    } catch (error) {
      console.error('Error copying markdown to clipboard:', error)
      alert('Failed to copy, check console for details')
    }
  }

  const handleCopyDemoMarkdown = async () => {
    if (!demoPRD) return
    try {
      const markdownText = formatPRDAsMarkdown(demoPRD)
      await navigator.clipboard.writeText(markdownText)
      setDemoCopied(true)
      setTimeout(() => setDemoCopied(false), 2000)
    } catch (error) {
      console.error('Error copying demo markdown:', error)
    }
  }

  const handleClusterFeedback = async () => {
    setIsLoading(true)
    try {
      let response
      if (uploadedFile) {
        const formData = new FormData()
        formData.append('file', uploadedFile)
        response = await fetch(`${API_BASE_URL}/feedback/cluster-csv`, {
          method: 'POST',
          body: formData,
        })
      } else {
        response = await fetch(`${API_BASE_URL}/feedback/cluster`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ raw_feedback: rawFeedback }),
        })
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const errorMessage = errorData.detail || `Server returned status code ${response.status}`
        throw new Error(errorMessage)
      }

      const data = await response.json()
      setClusters(data)
      setTimeout(() => {
        document.getElementById('workspace-clusters')?.scrollIntoView({ behavior: 'smooth' })
      }, 100)
    } catch (error) {
      console.error('Error clustering feedback:', error)
      const isNetworkError = error.message?.includes('Failed to fetch') || error.name === 'TypeError'
      const displayMsg = isNetworkError
        ? 'Server is waking up (Render cold start) or unreachable. Please wait ~30 seconds and try again.'
        : error.message
      alert(`Failed to cluster feedback: ${displayMsg}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleGeneratePRD = async (cluster) => {
    setLoadingPRDFor(cluster.theme_name)
    try {
      const response = await fetch(`${API_BASE_URL}/feedback/prd`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cluster),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const errorMessage = errorData.detail || `Server returned status code ${response.status}`
        throw new Error(errorMessage)
      }

      const prdData = await response.json()
      setGeneratedPRDs((prev) => ({
        ...prev,
        [cluster.theme_name]: prdData,
      }))
    } catch (error) {
      console.error('Error generating PRD:', error)
      const isNetworkError = error.message?.includes('Failed to fetch') || error.name === 'TypeError'
      const displayMsg = isNetworkError
        ? 'Server is waking up (Render cold start) or unreachable. Please wait ~30 seconds and try again.'
        : error.message
      alert(`Failed to generate PRD: ${displayMsg}`)
    } finally {
      setLoadingPRDFor(null)
    }
  }

  return (
    <div className="page-wrapper">
      {/* Noise Texture Overlay */}
      <div className="noise-overlay" aria-hidden="true" />

      {/* =========================================================================
         LANDING PAGE VIEW
         ========================================================================= */}
      {viewMode === 'landing' ? (
        <>
          {/* Navigation Bar */}
          <header className="navbar-container">
            <nav className="navbar">
              <div className="nav-left animate-fade-up" style={{ '--delay': '0.1s' }}>
                <a href="#" className="logo-link" aria-label="EchoInsight Home">
                  <svg className="logo-icon" width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="4" y="5" width="20" height="4.5" rx="2.25" fill="#FFFFFF" />
                    <rect x="4" y="12" width="13" height="4.5" rx="2.25" fill="#FFFFFF" fillOpacity="0.75" />
                    <rect x="4" y="19" width="20" height="4.5" rx="2.25" fill="#FFFFFF" />
                    <circle cx="22.5" cy="14.25" r="2.5" fill="#9A9A9A" />
                  </svg>
                  <span className="logo-wordmark">EchoInsight</span>
                </a>
              </div>

              <div className="nav-center animate-fade-up" style={{ '--delay': '0.2s' }}>
                <button type="button" onClick={scrollToDemo} className="nav-pill shine-effect">
                  How It Works
                </button>
                <button type="button" onClick={scrollToDemo} className="nav-pill shine-effect">
                  Clusters
                </button>
                <button type="button" onClick={scrollToDemo} className="nav-pill shine-effect">
                  PRD Generator
                </button>
              </div>

              <div className="nav-right animate-fade-up" style={{ '--delay': '0.3s' }}>
                <button type="button" onClick={switchToWorkspace} className="btn-solid shine-effect nav-cta">
                  Try It Free
                </button>
              </div>
            </nav>
          </header>

          {/* Hero Section */}
          <section className="hero-section" ref={heroRef}>
            <canvas ref={canvasRef} className="hero-particles-canvas" aria-hidden="true" />

            <div className="hero-container">
              <div className="hero-badge animate-fade-up" style={{ '--delay': '0.4s' }}>
                <span className="badge-pulse-dot" aria-hidden="true" />
                <span>AI-Powered Feedback Intelligence</span>
              </div>

              <h1 className="hero-headline">
                <span className="headline-line animate-fade-up" style={{ '--delay': '0.5s' }}>
                  Turn customer feedback into
                </span>
                <span className="headline-line animate-fade-up" style={{ '--delay': '0.6s' }}>
                  prioritized <span className="serif-emphasized">PRDs</span> in seconds.
                </span>
              </h1>

              <p className="hero-subheadline animate-fade-up" style={{ '--delay': '0.7s' }}>
                Paste raw feedback, get RICE-scored themes and structured product requirement docs — powered by Gemini and semantic memory.
              </p>

              <div className="hero-buttons-row animate-fade-up" style={{ '--delay': '0.9s' }}>
                <button type="button" onClick={switchToWorkspace} className="btn-solid shine-effect hero-btn">
                  Try It Free
                </button>
                <button type="button" onClick={scrollToDemo} className="btn-ghost shine-effect hero-btn">
                  See How It Works
                </button>
              </div>

              <div className="hero-stats-row animate-fade-up" style={{ '--delay': '1.1s' }}>
                <div className="stat-fact-item">
                  <svg className="stat-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="2" y="2" width="20" height="8" rx="2" ry="2" />
                    <rect x="2" y="14" width="20" height="8" rx="2" ry="2" />
                    <line x1="6" y1="6" x2="6.01" y2="6" />
                    <line x1="6" y1="18" x2="6.01" y2="18" />
                  </svg>
                  <span>3 AI-powered endpoints</span>
                </div>
                <div className="stat-fact-item">
                  <svg className="stat-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <ellipse cx="12" cy="5" rx="9" ry="3" />
                    <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
                    <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
                  </svg>
                  <span>RAG-based semantic memory</span>
                </div>
                <div className="stat-fact-item">
                  <svg className="stat-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                  </svg>
                  <span>RICE-scored prioritization</span>
                </div>
              </div>
            </div>
          </section>

          {/* Landing Page Automated Typewriter Demo Section */}
          <section id="demo-section" className="tool-section scroll-reveal">
            <div className="tool-container">
              <div className="tool-header">
                <span className="eyebrow-tag">AUTONOMOUS FEEDBACK PIPELINE</span>
                <h2 className="tool-title">EchoInsight Engine Demo</h2>
                <p className="tool-subtitle">
                  Watch the engine automatically analyze raw feedback, calculate RICE scores, and generate PRDs in real-time.
                </p>
              </div>

              {/* Read-Only Demo Input Card with Animated Cursor */}
              <div className="input-card demo-card-disabled scroll-reveal">
                {/* Simulated Animated Cursor */}
                {(demoState === 'moving_cursor' || demoState === 'clicking') && (
                  <div
                    className={`demo-animated-cursor ${
                      demoState === 'moving_cursor' || demoState === 'clicking' ? 'on-button' : ''
                    } ${demoState === 'clicking' ? 'clicking' : ''}`}
                    aria-hidden="true"
                  >
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path
                        d="M3 3L10.07 19.97L13.58 13.58L19.97 10.07L3 3Z"
                        fill="#FFFFFF"
                        stroke="#000000"
                        strokeWidth="1.5"
                        strokeLinejoin="round"
                      />
                    </svg>
                    {demoState === 'clicking' && <span className="cursor-click-ripple" />}
                  </div>
                )}

                <div className="demo-read-only-banner">
                  <span className="badge-pulse-dot" aria-hidden="true" />
                  <span>AUTOMATED LIVE DEMO — READ ONLY</span>
                </div>

                <span className="eyebrow-tag">FEEDBACK INPUT</span>
                <textarea
                  className="feedback-textarea demo-disabled-input"
                  rows={6}
                  value={demoText + (demoState === 'typing' ? '▌' : '')}
                  readOnly
                  disabled
                  aria-label="Automated demo feedback preview"
                />

                <div className="input-divider">
                  <span>OR</span>
                </div>

                <div className="csv-upload-container">
                  <label className="file-input-label demo-disabled-input">
                    <span className="eyebrow-tag">FEEDBACK CSV FILE</span>
                    <input type="file" disabled className="file-input" />
                  </label>
                </div>

                <div className="actions-container">
                  <button
                    type="button"
                    className={`btn-solid cluster-button demo-disabled-button ${
                      demoState === 'clicking' ? 'active-click-pulse' : ''
                    }`}
                    disabled
                  >
                    {demoState === 'clustering' ? 'Clustering...' : 'Cluster Feedback'}
                  </button>
                </div>
              </div>

              {/* Demo Clusters Output */}
              {demoClusters.length > 0 && (
                <div className="clusters-section scroll-reveal">
                  <div className="clusters-header">
                    <span className="eyebrow-tag">DEMO ANALYSIS & PRIORITIZATION</span>
                    <h2 className="clusters-heading">Feedback Clusters (Auto-Generated)</h2>
                  </div>
                  <div className="clusters-list">
                    {demoClusters.map((cluster, index) => (
                      <div key={index} className="cluster-card scroll-reveal">
                        <h3 className="cluster-title">{cluster.theme_name}</h3>

                        <div className="cluster-meta-grid">
                          <div className="stat-card rice-stat">
                            <span className="eyebrow-tag stat-label">RICE SCORE</span>
                            <span className="rice-hero-score">
                              {Number(cluster.rice_score).toFixed(1)}
                            </span>
                          </div>
                          <div className="stat-card freq-stat">
                            <span className="eyebrow-tag stat-label">FREQUENCY</span>
                            <span className="stat-value freq-value">
                              {cluster.frequency} <span className="stat-unit">mentions</span>
                            </span>
                          </div>
                          <div className="stat-card affected-stat">
                            <span className="eyebrow-tag stat-label">AFFECTED USERS</span>
                            <span className="stat-value affected-value">
                              👥 {cluster.affected_count} <span className="stat-unit">reports</span>
                            </span>
                          </div>
                          {cluster.negative_feedback_count > 0 && (
                            <div className="stat-card friction-stat">
                              <span className="eyebrow-tag stat-label">FRICTION / BUGS</span>
                              <span className="stat-value friction-value">
                                🚨 {cluster.negative_feedback_count} <span className="stat-unit">issues</span>
                              </span>
                            </div>
                          )}
                        </div>

                        <div className="feedback-section">
                          <span className="eyebrow-tag section-eyebrow">CLASSIFIED FEEDBACK</span>
                          <ul className="feedback-list">
                            {cluster.feedback_items.map((item, itemIdx) => (
                              <li key={itemIdx} className="feedback-item">
                                <span className="feedback-text">{item.text}</span>
                                {item.similar_past_count > 0 && (
                                  <span className="repeat-badge">
                                    🔁 Seen {item.similar_past_count}x before
                                  </span>
                                )}
                                <span className="feedback-tags">
                                  <span className="tag sentiment-tag">{item.sentiment}</span>
                                  <span className="tag intent-tag">{item.intent}</span>
                                  <span className="tag urgency-tag">{item.urgency}</span>
                                </span>
                              </li>
                            ))}
                          </ul>
                        </div>

                        {/* Demo Generated PRD */}
                        {index === 0 && demoPRD && (
                          <div className="prd-card scroll-reveal">
                            <h4 className="prd-title">{demoPRD.title}</h4>

                            <span className="eyebrow-tag prd-section-eyebrow">PROBLEM STATEMENT</span>
                            <p className="prd-text">{demoPRD.problem_statement}</p>

                            <span className="eyebrow-tag prd-section-eyebrow">USER STORIES</span>
                            <ul className="prd-list">
                              {demoPRD.user_stories.map((story, i) => (
                                <li key={i}>{story}</li>
                              ))}
                            </ul>

                            <span className="eyebrow-tag prd-section-eyebrow">ACCEPTANCE CRITERIA</span>
                            <ul className="prd-list">
                              {demoPRD.acceptance_criteria.map((criteria, i) => (
                                <li key={i}>{criteria}</li>
                              ))}
                            </ul>

                            <span className="eyebrow-tag prd-section-eyebrow">KPIS</span>
                            <ul className="prd-list">
                              {demoPRD.kpis.map((kpi, i) => (
                                <li key={i}>{kpi}</li>
                              ))}
                            </ul>

                            <button
                              type="button"
                              className="btn-ghost shine-effect copy-markdown-button"
                              onClick={handleCopyDemoMarkdown}
                            >
                              {demoCopied ? 'Copied!' : 'Copy as Markdown'}
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Launcher CTA Banner below Demo */}
              <div className="demo-launcher-banner scroll-reveal">
                <div className="launcher-text-col">
                  <span className="eyebrow-tag">READY FOR YOUR OWN FEEDBACK?</span>
                  <h3 className="launcher-headline">Analyze Your Customer Feedback Live</h3>
                  <p className="launcher-subtext">
                    Launch the interactive workspace to paste custom user feedback or upload CSV datasets.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={switchToWorkspace}
                  className="btn-solid shine-effect launcher-cta-btn"
                >
                  Try It Free — Launch Workspace →
                </button>
              </div>
            </div>
          </section>
        </>
      ) : (
        /* =========================================================================
           INTERACTIVE WORKING WORKSPACE VIEW
           ========================================================================= */
        <div className="workspace-wrapper">
          {/* Workspace Navigation Header */}
          <header className="navbar-container">
            <nav className="navbar">
              <div className="nav-left">
                <a href="#" onClick={switchToLanding} className="logo-link" aria-label="EchoInsight Home">
                  <svg className="logo-icon" width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="4" y="5" width="20" height="4.5" rx="2.25" fill="#FFFFFF" />
                    <rect x="4" y="12" width="13" height="4.5" rx="2.25" fill="#FFFFFF" fillOpacity="0.75" />
                    <rect x="4" y="19" width="20" height="4.5" rx="2.25" fill="#FFFFFF" />
                    <circle cx="22.5" cy="14.25" r="2.5" fill="#9A9A9A" />
                  </svg>
                  <span className="logo-wordmark">EchoInsight</span>
                  <span className="workspace-pill-badge">INTERACTIVE WORKSPACE</span>
                </a>
              </div>

              <div className="nav-right">
                <button type="button" onClick={switchToLanding} className="btn-ghost shine-effect nav-cta">
                  ← Back to Product Overview
                </button>
              </div>
            </nav>
          </header>

          {/* Interactive Tool Container */}
          <main className="tool-section">
            <div className="tool-container">
              <div className="tool-header">
                <span className="eyebrow-tag">INTERACTIVE PIPELINE</span>
                <h1 className="tool-title">EchoInsight Workspace</h1>
                <p className="tool-subtitle">
                  Paste raw customer feedback below (one item per line) or upload a CSV file to generate RICE-scored themes and PRDs.
                </p>
              </div>

              {/* Fully Working Input Container */}
              <div className="input-card">
                <span className="eyebrow-tag">FEEDBACK INPUT</span>
                <textarea
                  className="feedback-textarea"
                  rows={8}
                  value={rawFeedback}
                  aria-label="Paste customer feedback here"
                  onChange={(e) => {
                    setRawFeedback(e.target.value)
                    if (uploadedFile) setUploadedFile(null)
                  }}
                  disabled={!!uploadedFile}
                  placeholder={
                    uploadedFile
                      ? `CSV file selected (${uploadedFile.name}). Clear file below to paste text.`
                      : "Users are asking for dark mode support\nThe export button crashes when exporting large reports\nNeed easier user onboarding steps"
                  }
                />

                <div className="input-divider">
                  <span>OR</span>
                </div>

                <div className="csv-upload-container">
                  <label className="file-input-label">
                    <span className="eyebrow-tag">FEEDBACK CSV FILE</span>
                    <input
                      type="file"
                      accept=".csv"
                      className="file-input"
                      aria-label="Upload feedback CSV file"
                      onChange={(e) => {
                        const file = e.target.files[0] || null
                        setUploadedFile(file)
                        if (file) setRawFeedback('')
                      }}
                    />
                  </label>

                  {uploadedFile && (
                    <div className="file-status">
                      <span className="selected-filename">Selected: {uploadedFile.name}</span>
                      <button
                        type="button"
                        className="btn-ghost shine-effect clear-file-button"
                        onClick={() => setUploadedFile(null)}
                      >
                        Clear File
                      </button>
                    </div>
                  )}
                </div>

                <div className="actions-container">
                  <button
                    type="button"
                    className="btn-solid shine-effect cluster-button"
                    onClick={handleClusterFeedback}
                    disabled={isLoading}
                  >
                    {isLoading ? 'Clustering...' : 'Cluster Feedback'}
                  </button>
                </div>
              </div>

              {/* Live Working Clusters Section */}
              {clusters.length > 0 && (
                <section id="workspace-clusters" className="clusters-section">
                  <div className="clusters-header">
                    <span className="eyebrow-tag">ANALYSIS & PRIORITIZATION</span>
                    <h2 className="clusters-heading">Feedback Clusters</h2>
                  </div>
                  <div className="clusters-list">
                    {clusters.map((cluster, index) => {
                      const prd = generatedPRDs[cluster.theme_name]
                      const isGeneratingPRD = loadingPRDFor === cluster.theme_name
                      const isCopied = copiedPRDFor === cluster.theme_name

                      return (
                        <div key={cluster.theme_name || index} className="cluster-card">
                          <h3 className="cluster-title">{cluster.theme_name}</h3>

                          <div className="cluster-meta-grid">
                            <div className="stat-card rice-stat">
                              <span className="eyebrow-tag stat-label">RICE SCORE</span>
                              <span className="rice-hero-score">
                                {Number(cluster.rice_score || 0).toFixed(1)}
                              </span>
                            </div>
                            <div className="stat-card freq-stat">
                              <span className="eyebrow-tag stat-label">FREQUENCY</span>
                              <span className="stat-value freq-value">
                                {cluster.frequency} <span className="stat-unit">mentions</span>
                              </span>
                            </div>
                            <div className="stat-card affected-stat">
                              <span className="eyebrow-tag stat-label">AFFECTED USERS</span>
                              <span className="stat-value affected-value">
                                👥 {cluster.affected_count || cluster.frequency || 0} <span className="stat-unit">reports</span>
                              </span>
                            </div>
                            {cluster.negative_feedback_count > 0 && (
                              <div className="stat-card friction-stat">
                                <span className="eyebrow-tag stat-label">FRICTION / BUGS</span>
                                <span className="stat-value friction-value">
                                  🚨 {cluster.negative_feedback_count} <span className="stat-unit">issues</span>
                                </span>
                              </div>
                            )}
                          </div>

                          <div className="feedback-section">
                            <span className="eyebrow-tag section-eyebrow">CLASSIFIED FEEDBACK</span>
                            <ul className="feedback-list">
                              {cluster.feedback_items?.map((item, itemIdx) => (
                                <li key={itemIdx} className="feedback-item">
                                  <span className="feedback-text">{item.text}</span>
                                  {item.similar_past_count > 0 && (
                                    <span className="repeat-badge">
                                      🔁 Seen {item.similar_past_count}x before
                                    </span>
                                  )}
                                  <span className="feedback-tags">
                                    <span className="tag sentiment-tag">{item.sentiment}</span>
                                    <span className="tag intent-tag">{item.intent}</span>
                                    <span className="tag urgency-tag">{item.urgency}</span>
                                  </span>
                                </li>
                              ))}
                            </ul>
                          </div>

                          <button
                            type="button"
                            className="btn-solid shine-effect generate-prd-button"
                            onClick={() => handleGeneratePRD(cluster)}
                            disabled={isGeneratingPRD}
                          >
                            {isGeneratingPRD ? 'Generating...' : 'Generate PRD'}
                          </button>

                          {prd && (
                            <div className="prd-card">
                              <h4 className="prd-title">{prd.title}</h4>

                              <span className="eyebrow-tag prd-section-eyebrow">PROBLEM STATEMENT</span>
                              <p className="prd-text">{prd.problem_statement}</p>

                              <span className="eyebrow-tag prd-section-eyebrow">USER STORIES</span>
                              <ul className="prd-list">
                                {prd.user_stories?.map((story, i) => (
                                  <li key={i}>{story}</li>
                                ))}
                              </ul>

                              <span className="eyebrow-tag prd-section-eyebrow">ACCEPTANCE CRITERIA</span>
                              <ul className="prd-list">
                                {prd.acceptance_criteria?.map((criteria, i) => (
                                  <li key={i}>{criteria}</li>
                                ))}
                              </ul>

                              <span className="eyebrow-tag prd-section-eyebrow">KPIS</span>
                              <ul className="prd-list">
                                {prd.kpis?.map((kpi, i) => (
                                  <li key={i}>{kpi}</li>
                                ))}
                              </ul>

                              <button
                                type="button"
                                className="btn-ghost shine-effect copy-markdown-button"
                                onClick={() => handleCopyMarkdown(cluster, prd)}
                              >
                                {isCopied ? 'Copied!' : 'Copy as Markdown'}
                              </button>
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </section>
              )}
            </div>
          </main>
        </div>
      )}

      {/* Footer */}
      <footer className="page-footer">
        <div className="footer-container">
          <p>© {new Date().getFullYear()} EchoInsight. Powered by Gemini & Semantic Vector Memory.</p>
        </div>
      </footer>
    </div>
  )
}

export default App
