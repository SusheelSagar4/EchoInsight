import { useState } from 'react'
import './App.css'

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
      // 1. Format PRD data into Markdown string structure
      const markdownText = formatPRDAsMarkdown(prd)

      // 2. Write text to user's system clipboard using standard browser API
      await navigator.clipboard.writeText(markdownText)

      // 3. Update copied state to display "Copied!" feedback
      setCopiedPRDFor(cluster.theme_name)

      // 4. Automatically reset copied state back to null after 2000ms
      setTimeout(() => {
        setCopiedPRDFor(null)
      }, 2000)
    } catch (error) {
      // Handle clipboard API failures
      console.error('Error copying markdown to clipboard:', error)
      alert('Failed to copy, check console for details')
    }
  }

  // Handler function triggered when user clicks the "Cluster Feedback" button
  const handleClusterFeedback = async () => {
    // 1. Indicate loading start
    setIsLoading(true)

    try {
      let response

      if (uploadedFile) {
        // Path A: If a CSV file is selected, construct FormData and POST to /feedback/cluster-csv
        const formData = new FormData()
        formData.append('file', uploadedFile)

        response = await fetch('http://127.0.0.1:8000/feedback/cluster-csv', {
          method: 'POST',
          body: formData, // FormData automatically sets multipart/form-data boundary header
        })
      } else {
        // Path B: If no CSV file is selected, send raw feedback text as JSON to /feedback/cluster
        response = await fetch('http://127.0.0.1:8000/feedback/cluster', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ raw_feedback: rawFeedback }),
        })
      }

      if (!response.ok) {
        throw new Error(`Server returned status code ${response.status}`)
      }

      // On success: parse JSON, log to console, and store in clusters state
      const data = await response.json()
      console.log('Clustering result:', data)
      setClusters(data)
    } catch (error) {
      // On failure: log error to console and show user alert
      console.error('Error clustering feedback:', error)
      alert('Failed to cluster feedback, check console for details')
    } finally {
      // Always reset loading state when request completes (success or failure)
      setIsLoading(false)
    }
  }

  // Handler function triggered when user clicks "Generate PRD" on a cluster card
  const handleGeneratePRD = async (cluster) => {
    // 1. Set per-card loading state to active cluster's theme_name
    setLoadingPRDFor(cluster.theme_name)

    try {
      // 2. Send POST request to backend /feedback/prd endpoint with cluster object
      const response = await fetch('http://127.0.0.1:8000/feedback/prd', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(cluster),
      })

      if (!response.ok) {
        throw new Error(`Server returned status code ${response.status}`)
      }

      // 3. Parse PRD object and save into generatedPRDs dictionary keyed by theme_name
      const prdData = await response.json()
      setGeneratedPRDs((prev) => ({
        ...prev,
        [cluster.theme_name]: prdData,
      }))
    } catch (error) {
      // 4. Handle PRD generation error
      console.error('Error generating PRD:', error)
      alert('Failed to generate PRD, check console for details')
    } finally {
      // 5. Clear per-card loading state regardless of outcome
      setLoadingPRDFor(null)
    }
  }

  return (
    <div className="app-container">
      {/* App Header */}
      <header className="app-header">
        <span className="eyebrow">AUTONOMOUS FEEDBACK PIPELINE</span>
        <h1 className="app-title">EchoInsight — Feedback to PRD Pipeline</h1>
        <p className="app-subtitle">
          Paste raw customer feedback below (one item per line) or upload a CSV file
        </p>
      </header>

      {/* Input container: Textarea and CSV Upload */}
      <div className="input-container">
        <span className="eyebrow input-eyebrow">FEEDBACK INPUT</span>
        <textarea
          className="feedback-textarea"
          rows={8}
          value={rawFeedback}
          onChange={(e) => {
            setRawFeedback(e.target.value)
            if (uploadedFile) setUploadedFile(null) // Clear file selection when user types in textarea
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
            <span className="eyebrow file-eyebrow">FEEDBACK CSV FILE</span>
            <input
              type="file"
              accept=".csv"
              className="file-input"
              onChange={(e) => {
                const file = e.target.files[0] || null
                setUploadedFile(file)
                if (file) setRawFeedback('') // Clear text input when a file is selected
              }}
            />
          </label>

          {/* Display selected file name and clear button */}
          {uploadedFile && (
            <div className="file-status">
              <span className="selected-filename">Selected: {uploadedFile.name}</span>
              <button
                type="button"
                className="clear-file-button"
                onClick={() => setUploadedFile(null)}
              >
                Clear File
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Action button to initiate feedback clustering */}
      <div className="actions-container">
        <button
          className="cluster-button"
          onClick={handleClusterFeedback}
          disabled={isLoading}
        >
          {isLoading ? 'Clustering...' : 'Cluster Feedback'}
        </button>
      </div>

      {/* Clusters Section: Rendered only when clusters array is non-empty */}
      {clusters.length > 0 && (
        <div className="clusters-container">
          <div className="clusters-header">
            <span className="eyebrow">ANALYSIS & PRIORITIZATION</span>
            <h2 className="clusters-heading">Feedback Clusters</h2>
          </div>
          <div className="clusters-list">
            {clusters.map((cluster, index) => {
              const prd = generatedPRDs[cluster.theme_name]
              const isGeneratingPRD = loadingPRDFor === cluster.theme_name
              const isCopied = copiedPRDFor === cluster.theme_name

              return (
                <div key={cluster.theme_name || index} className="cluster-card">
                  {/* Theme Name Subheading */}
                  <h3 className="cluster-title">{cluster.theme_name}</h3>

                  {/* Metadata: RICE score (rounded to 1 decimal place) & Frequency */}
                  <div className="cluster-meta-grid">
                    <div className="stat-card rice-stat">
                      <span className="eyebrow stat-label">RICE SCORE</span>
                      <span className="stat-value rice-hero-score">
                        {Number(cluster.rice_score || 0).toFixed(1)}
                      </span>
                    </div>
                    <div className="stat-card freq-stat">
                      <span className="eyebrow stat-label">FREQUENCY</span>
                      <span className="stat-value freq-value">
                        {cluster.frequency} <span className="stat-unit">mentions</span>
                      </span>
                    </div>
                  </div>

                  {/* List of raw feedback items with sentiment, intent, and urgency */}
                  <div className="feedback-section">
                    <span className="eyebrow section-eyebrow">CLASSIFIED FEEDBACK</span>
                    <ul className="feedback-list">
                      {cluster.feedback_items?.map((item, itemIdx) => (
                        <li key={itemIdx} className="feedback-item">
                          <span className="feedback-text">{item.text}</span>
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
                    className="generate-prd-button"
                    onClick={() => handleGeneratePRD(cluster)}
                    disabled={isGeneratingPRD}
                  >
                    {isGeneratingPRD ? 'Generating...' : 'Generate PRD'}
                  </button>

                  {/* Render PRD Card when generated for this cluster */}
                  {prd && (
                    <div className="prd-card">
                      <h4 className="prd-title">{prd.title}</h4>

                      <span className="eyebrow prd-section-eyebrow">PROBLEM STATEMENT</span>
                      <p className="prd-text">{prd.problem_statement}</p>

                      <span className="eyebrow prd-section-eyebrow">USER STORIES</span>
                      <ul className="prd-list">
                        {prd.user_stories?.map((story, i) => (
                          <li key={i}>{story}</li>
                        ))}
                      </ul>

                      <span className="eyebrow prd-section-eyebrow">ACCEPTANCE CRITERIA</span>
                      <ul className="prd-list">
                        {prd.acceptance_criteria?.map((criteria, i) => (
                          <li key={i}>{criteria}</li>
                        ))}
                      </ul>

                      <span className="eyebrow prd-section-eyebrow">KPIS</span>
                      <ul className="prd-list">
                        {prd.kpis?.map((kpi, i) => (
                          <li key={i}>{kpi}</li>
                        ))}
                      </ul>

                      {/* Button to copy PRD in Markdown format */}
                      <button
                        className="copy-markdown-button"
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
        </div>
      )}
    </div>
  )
}

export default App

