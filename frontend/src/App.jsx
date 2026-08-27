import { useState, useEffect, useRef } from 'react'
import './App.css'

// Base URL for backend API requests, loaded from environment variables (sanitized to remove trailing slashes) or defaulting to live Render backend
const RAW_API_URL = import.meta.env.VITE_API_URL || 'https://echoinsight.onrender.com'
const API_BASE_URL = RAW_API_URL.replace(/\/+$/, '')

// Main functional component for the EchoInsight user interface
function App() {
  // State 1: Tracks the raw feedback text entered by the user in the textarea
  const [rawFeedback, setRawFeedback] = useState('')

  // State 2: Tracks whether the feedback clustering API request is currently loading
  const [isLoading, setIsLoading] = useState(false)

  // State 3: Stores the array of feedback clusters returned from the API
  const [clusters, setClusters] = useState([])

  // State 4: Maps cluster theme_names to their generated PRD objects ({ [theme_name]: prdObject })
  const [generatedPRDs, setGeneratedPRDs] = useState({})

  // State 5: Tracks which cluster theme_name is currently generating a PRD (null if none)
  const [loadingPRDFor, setLoadingPRDFor] = useState(null)

  // State 6: Stores the selected CSV file object (null if no file selected)
  const [uploadedFile, setUploadedFile] = useState(null)

  // State 7: Tracks which cluster theme_name currently shows "Copied!" feedback (null if none)
  const [copiedPRDFor, setCopiedPRDFor] = useState(null)

  // Refs for hero section and interactive particle canvas
  const heroRef = useRef(null)
  const canvasRef = useRef(null)

  // Interactive mouse particle system in the hero section
  useEffect(() => {
    const canvas = canvasRef.current
    const hero = heroRef.current
    if (!canvas || !hero) return

    // Respect prefers-reduced-motion
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

    // Generate 110 lightweight dust particles
    const particleCount = 110
    const particles = []

    for (let i = 0; i < particleCount; i++) {
      const baseVx = (Math.random() - 0.5) * 0.4
      const baseVy = (Math.random() - 0.5) * 0.4
      particles.push({
        x: Math.random() * (canvas.width || 1),
        y: Math.random() * (canvas.height || 1),
        baseVx,
        baseVy,
        vx: baseVx,
        vy: baseVy,
        radius: Math.random() * 1.8 + 1, // 1px to 2.8px
        opacity: Math.random() * 0.4 + 0.2, // 0.2 to 0.6 opacity
      })
    }

    const mouse = {
      x: -9999,
      y: -9999,
      isOver: false,
    }

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

    // Pause animation when hero is out of view
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

        // Soft mouse repulsion effect within 120px radius
        if (mouse.isOver) {
          const dx = p.x - mouse.x
          const dy = p.y - mouse.y
          const dist = Math.sqrt(dx * dx + dy * dy)
          const repulsionRadius = 120

          if (dist < repulsionRadius && dist > 0) {
            const force = (1 - dist / repulsionRadius) * 1.6
            const angle = Math.atan2(dy, dx)
            p.vx += Math.cos(angle) * force * 0.2
            p.vy += Math.sin(angle) * force * 0.2
          }
        }

        // Smoothly ease velocity back toward base velocity
        p.vx += (p.baseVx - p.vx) * 0.05
        p.vy += (p.baseVy - p.vy) * 0.05

        p.x += p.vx
        p.y += p.vy

        // Wrap around canvas boundaries
        if (p.x < 0) p.x = canvas.width
        if (p.x > canvas.width) p.x = 0
        if (p.y < 0) p.y = canvas.height
        if (p.y > canvas.height) p.y = 0

        // Draw particle
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
  }, [])

  // Scroll reveal observer for dynamic cluster and PRD cards
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
  }, [clusters, generatedPRDs])

  // Smooth scroll navigation helpers
  const scrollToTool = () => {
    document.getElementById('tool-section')?.scrollIntoView({ behavior: 'smooth' })
  }

  const scrollToClusters = () => {
    if (clusters.length > 0) {
      document.getElementById('clusters-section')?.scrollIntoView({ behavior: 'smooth' })
    } else {
      scrollToTool()
    }
  }

  // Helper function to format PRD object into structured Markdown text
  const formatPRDAsMarkdown = (prd) => {
    const userStories = (prd.user_stories || [])
      .map((story) => `- ${story}`)
      .join('\n')

    const acceptanceCriteria = (prd.acceptance_criteria || [])
      .map((criterion) => `- ${criterion}`)
      .join('\n')

    const kpis = (prd.kpis || []).map((kpi) => `- ${kpi}`).join('\n')

    return `# ${prd.title || ''}

## Problem Statement

${prd.problem_statement || ''}

## User Stories

${userStories}

## Acceptance Criteria

${acceptanceCriteria}

## KPIs

${kpis}`
  }

  // Handler function to copy PRD markdown to system clipboard
  const handleCopyMarkdown = async (cluster, prd) => {
    try {
      const markdownText = formatPRDAsMarkdown(prd)
      await navigator.clipboard.writeText(markdownText)
      setCopiedPRDFor(cluster.theme_name)
      setTimeout(() => {
        setCopiedPRDFor(null)
      }, 2000)
    } catch (error) {
      console.error('Error copying markdown to clipboard:', error)
      alert('Failed to copy, check console for details')
    }
  }

  // Handler function triggered when user clicks the "Cluster Feedback" button
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
          headers: {
            'Content-Type': 'application/json',
          },
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
        document.getElementById('clusters-section')?.scrollIntoView({ behavior: 'smooth' })
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

  // Handler function triggered when user clicks "Generate PRD" on a cluster card
  const handleGeneratePRD = async (cluster) => {
    setLoadingPRDFor(cluster.theme_name)
    try {
      const response = await fetch(`${API_BASE_URL}/feedback/prd`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
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
      {/* Fixed Subtle Noise Texture Overlay */}
      <div className="noise-overlay" aria-hidden="true" />

      {/* 3-Column Navigation Bar (sits above everything) */}
      <header className="navbar-container">
        <nav className="navbar">
          {/* Column 1: Logo */}
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

          {/* Column 2: Nav Links */}
          <div className="nav-center animate-fade-up" style={{ '--delay': '0.2s' }}>
            <button type="button" onClick={scrollToTool} className="nav-pill shine-effect">
              How It Works
            </button>
            <button type="button" onClick={scrollToClusters} className="nav-pill shine-effect">
              Clusters
            </button>
            <button type="button" onClick={scrollToTool} className="nav-pill shine-effect">
              PRD Generator
            </button>
          </div>

          {/* Column 3: Nav CTA */}
          <div className="nav-right animate-fade-up" style={{ '--delay': '0.3s' }}>
            <button type="button" onClick={scrollToTool} className="btn-solid shine-effect nav-cta">
              Try It Free
            </button>
          </div>
        </nav>
      </header>

      {/* Hero Section (Bottom-Anchored Layout) */}
      <section className="hero-section" ref={heroRef}>
        {/* Interactive Mouse Particle Canvas */}
        <canvas ref={canvasRef} className="hero-particles-canvas" aria-hidden="true" />

        <div className="hero-container">
          {/* Small Pill Badge */}
          <div className="hero-badge animate-fade-up" style={{ '--delay': '0.4s' }}>
            <span className="badge-pulse-dot" aria-hidden="true" />
            <span>AI-Powered Feedback Intelligence</span>
          </div>

          {/* Headline (Two Lines with Instrument Serif PRDs) */}
          <h1 className="hero-headline">
            <span className="headline-line animate-fade-up" style={{ '--delay': '0.5s' }}>
              Turn customer feedback into
            </span>
            <span className="headline-line animate-fade-up" style={{ '--delay': '0.6s' }}>
              prioritized <span className="serif-emphasized">PRDs</span> in seconds.
            </span>
          </h1>

          {/* Subheadline */}
          <p className="hero-subheadline animate-fade-up" style={{ '--delay': '0.7s' }}>
            Paste raw feedback, get RICE-scored themes and structured product requirement docs — powered by Gemini and semantic memory.
          </p>

          {/* Action Buttons */}
          <div className="hero-buttons-row animate-fade-up" style={{ '--delay': '0.9s' }}>
            <button type="button" onClick={scrollToTool} className="btn-solid shine-effect hero-btn">
              Try It Free
            </button>
            <button type="button" onClick={scrollToTool} className="btn-ghost shine-effect hero-btn">
              See How It Works
            </button>
          </div>

          {/* Stats Row at bottom of Hero */}
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

      {/* Main Tool Section (stays fully functional below hero) */}
      <main id="tool-section" className="tool-section scroll-reveal">
        <div className="tool-container">
          {/* Tool Header */}
          <div className="tool-header">
            <span className="eyebrow-tag">AUTONOMOUS FEEDBACK PIPELINE</span>
            <h2 className="tool-title">EchoInsight Engine</h2>
            <p className="tool-subtitle">
              Paste raw customer feedback below (one item per line) or upload a CSV file
            </p>
          </div>

          {/* Input Container: Textarea & CSV Upload */}
          <div className="input-card scroll-reveal">
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

            {/* Visual Divider */}
            <div className="input-divider">
              <span>OR</span>
            </div>

            {/* CSV File Upload Section */}
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

            {/* Action button to initiate feedback clustering */}
            <div className="actions-container">
              <button
                className="btn-solid shine-effect cluster-button"
                onClick={handleClusterFeedback}
                disabled={isLoading}
              >
                {isLoading ? 'Clustering...' : 'Cluster Feedback'}
              </button>
            </div>
          </div>

          {/* Clusters Section */}
          {clusters.length > 0 && (
            <section id="clusters-section" className="clusters-section scroll-reveal">
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
                    <div key={cluster.theme_name || index} className="cluster-card scroll-reveal">
                      {/* Theme Name Subheading */}
                      <h3 className="cluster-title">{cluster.theme_name}</h3>

                      {/* Metadata: RICE score, Frequency, Affected Users, Friction Points */}
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

                      {/* List of raw feedback items */}
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

                      {/* Button to generate PRD for this cluster */}
                      <button
                        className="btn-solid shine-effect generate-prd-button"
                        onClick={() => handleGeneratePRD(cluster)}
                        disabled={isGeneratingPRD}
                      >
                        {isGeneratingPRD ? 'Generating...' : 'Generate PRD'}
                      </button>

                      {/* Render PRD Card when generated for this cluster */}
                      {prd && (
                        <div className="prd-card scroll-reveal">
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

      {/* Clean Dark Footer */}
      <footer className="page-footer">
        <div className="footer-container">
          <p>© {new Date().getFullYear()} EchoInsight. Powered by Gemini & Semantic Vector Memory.</p>
        </div>
      </footer>
    </div>
  )
}

export default App
