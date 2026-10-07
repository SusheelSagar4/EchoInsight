import { useState, useEffect, useRef } from 'react'

const EXAMPLE_GOALS = [
  {
    id: 'goal_1',
    label: 'Full Pipeline (PRD + Backlog)',
    goal: 'Find the most important recurring issue, create a PRD, add it to the backlog',
  },
  {
    id: 'goal_2',
    label: 'Targeted Topic Backlog',
    goal: 'Find the top recurring complaint about checkout payment failures and create a backlog item',
  },
  {
    id: 'goal_3',
    label: 'Read-Only Trend Query',
    goal: 'Which problem is getting worse?',
  },
]

const TERMINAL_STATUSES = [
  'completed',
  'rejected_by_human',
  'approval_timeout',
  'halted_quota',
  'max_steps_reached',
  'invalid_planner_output',
  'failed',
]

function AgentView({ apiBaseUrl }) {
  const [goalText, setGoalText] = useState('')
  const [activeRunId, setActiveRunId] = useState(null)
  const [runState, setRunState] = useState(null)
  const [isStarting, setIsStarting] = useState(false)
  const [isApproving, setIsApproving] = useState(false)
  const [apiError, setApiError] = useState(null)
  const [isColdStarting, setIsColdStarting] = useState(false)

  const pollTimerRef = useRef(null)

  // Helper to format ISO timestamp into local time
  const formatTime = (isoStr) => {
    if (!isoStr) return ''
    try {
      const dt = new Date(isoStr)
      return dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    } catch {
      return ''
    }
  }

  // Poll GET /agent/runs/{id}
  useEffect(() => {
    if (!activeRunId) return

    const fetchRunStatus = async () => {
      try {
        const res = await fetch(`${apiBaseUrl}/agent/runs/${activeRunId}`)
        if (!res.ok) {
          if (res.status === 502 || res.status === 503 || res.status === 504) {
            setIsColdStarting(true)
          } else {
            setApiError(`Server error (${res.status}) while fetching run status.`)
          }
          return
        }

        setIsColdStarting(false)
        setApiError(null)
        const data = await res.json()
        setRunState(data)

        // Stop polling if terminal status reached
        if (TERMINAL_STATUSES.includes(data.status)) {
          if (pollTimerRef.current) {
            clearInterval(pollTimerRef.current)
            pollTimerRef.current = null
          }
        }
      } catch (err) {
        setIsColdStarting(true)
        console.warn('Polling error:', err)
      }
    }

    // Initial fetch immediately
    fetchRunStatus()

    // Poll every 1.5s (1500ms)
    pollTimerRef.current = setInterval(fetchRunStatus, 1500)

    return () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current)
        pollTimerRef.current = null
      }
    }
  }, [activeRunId, apiBaseUrl])

  // Handle Start Run
  const handleStartRun = async () => {
    if (!goalText.trim() || isStarting) return

    setIsStarting(true)
    setApiError(null)
    setIsColdStarting(false)
    setRunState(null)
    setActiveRunId(null)

    try {
      const res = await fetch(`${apiBaseUrl}/agent/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal: goalText.trim() }),
      })

      if (!res.ok) {
        if (res.status === 502 || res.status === 503 || res.status === 504) {
          setIsColdStarting(true)
        } else {
          setApiError(`Failed to start agent run (${res.status}).`)
        }
        setIsStarting(false)
        return
      }

      const data = await res.json()
      setActiveRunId(data.run_id)
      setRunState({ run_id: data.run_id, status: data.status, trace: [] })
    } catch (err) {
      setIsColdStarting(true)
      setApiError('Unable to connect to backend server. It may be starting up on Render.')
      console.error(err)
    } finally {
      setIsStarting(false)
    }
  }

  // Handle Approve / Reject
  const handleApproveDecision = async (approved) => {
    if (!activeRunId || isApproving) return

    setIsApproving(true)
    try {
      const res = await fetch(`${apiBaseUrl}/agent/runs/${activeRunId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved }),
      })

      if (!res.ok) {
        setApiError(`Approval request failed (${res.status}).`)
        return
      }

      // Immediately fetch updated status
      const statusRes = await fetch(`${apiBaseUrl}/agent/runs/${activeRunId}`)
      if (statusRes.ok) {
        const data = await statusRes.json()
        setRunState(data)
      }
    } catch (err) {
      setApiError('Network error while submitting approval decision.')
      console.error(err)
    } finally {
      setIsApproving(false)
    }
  }

  // Find verified item ID from trace or state
  const getVerifiedItemId = () => {
    if (!runState || !runState.trace) return null

    // Check verification events
    for (const evt of runState.trace) {
      if (evt.event_type === 'verification' && evt.passed && evt.item_id) {
        return evt.item_id
      }
    }

    // Check tool results for create_backlog_item
    for (const evt of runState.trace) {
      if (evt.event_type === 'tool_result' && evt.result?.ok && evt.result?.data?.id) {
        return evt.result.data.id
      }
    }

    // Regex search in final answer or trace text for ENG-XXX
    if (runState.final_answer) {
      const match = runState.final_answer.match(/ENG-\d+/i)
      if (match) return match[0]
    }

    return null
  }

  // Event metadata visual mapping helper
  const getEventMeta = (evt) => {
    const type = (evt.event_type || '').toUpperCase()
    switch (type) {
      case 'GOAL_RECEIVED':
        return { icon: '🎯', title: 'Goal Received', cardClass: 'card-goal' }
      case 'DECISION':
        return { icon: '🧠', title: 'Planner Decision', cardClass: 'card-decision' }
      case 'TOOL_CALL':
        return { icon: '⚙️', title: 'Executing Tool', cardClass: 'card-tool-call' }
      case 'TOOL_RESULT':
        return evt.result?.ok
          ? { icon: '✅', title: 'Tool Success', cardClass: 'card-success' }
          : { icon: '❌', title: `Tool Failure (${evt.result?.error_type || 'error'})`, cardClass: 'card-failure' }
      case 'RETRY':
        return { icon: '⏳', title: 'Retrying Transient Error', cardClass: 'card-retry' }
      case 'APPROVAL_REQUESTED':
        return { icon: '⚠️', title: 'Approval Requested', cardClass: 'card-approval-req' }
      case 'APPROVAL_RESULT':
        return evt.approved
          ? { icon: '🛡️', title: 'Human Approved', cardClass: 'card-approval-pass' }
          : { icon: '🛡️', title: 'Human Rejected', cardClass: 'card-approval-fail' }
      case 'VERIFICATION':
        return evt.passed
          ? { icon: '🔍', title: `Verified Item ${evt.item_id || ''}`, cardClass: 'card-verify-pass' }
          : { icon: '✋', title: 'Verification Guard Refusal', cardClass: 'card-verify-fail' }
      case 'FINISH':
        return { icon: '🎉', title: 'Task Completed', cardClass: 'card-finish' }
      case 'HALTED':
        return { icon: '🛑', title: 'Run Halted', cardClass: 'card-halted' }
      default:
        return { icon: '📌', title: type, cardClass: 'card-default' }
    }
  }

  const isTerminal = runState && TERMINAL_STATUSES.includes(runState.status)
  const verifiedItemId = getVerifiedItemId()

  return (
    <div className="agent-view-container">
      {/* Header & Subtitle */}
      <div className="tool-header">
        <span className="eyebrow-tag">AUTONOMOUS AGENT ENGINE</span>
        <h1 className="tool-title">EchoInsight Agent Control Center</h1>
        <p className="tool-subtitle">
          Execute multi-step product goals with live trace monitoring, swappable planners, and human approval safety controls.
        </p>
      </div>

      {/* Backend Cold Start Warning Banner */}
      {isColdStarting && (
        <div className="cold-start-banner animate-fade-up">
          <div className="banner-content">
            <span className="banner-spinner" aria-hidden="true" />
            <div>
              <strong>Backend Service Spinning Up...</strong>
              <p>The Render server is cold-starting. Please wait 15–30 seconds while the backend initializes.</p>
            </div>
          </div>
        </div>
      )}

      {/* General Error Banner */}
      {apiError && !isColdStarting && (
        <div className="error-banner animate-fade-up">
          <span>⚠️ {apiError}</span>
        </div>
      )}

      {/* Input Card with Goal Textarea & Example Buttons */}
      <div className="input-card agent-input-card">
        <span className="eyebrow-tag">NATURAL LANGUAGE GOAL</span>

        {/* Example Goal Quick Buttons */}
        <div className="example-goals-container">
          <span className="example-goals-label">Try Example Goal:</span>
          <div className="example-goals-pills">
            {EXAMPLE_GOALS.map((eg) => (
              <button
                key={eg.id}
                type="button"
                className="btn-ghost shine-effect example-goal-pill"
                onClick={() => setGoalText(eg.goal)}
              >
                {eg.label}
              </button>
            ))}
          </div>
        </div>

        <textarea
          className="feedback-textarea agent-textarea"
          rows={3}
          value={goalText}
          aria-label="Enter natural language agent goal"
          onChange={(e) => setGoalText(e.target.value)}
          placeholder="e.g. Find the most important recurring issue, create a PRD, add it to the backlog"
        />

        <div className="actions-container">
          <button
            type="button"
            className="btn-solid shine-effect cluster-button run-agent-btn"
            onClick={handleStartRun}
            disabled={isStarting || !goalText.trim()}
          >
            {isStarting ? (
              <>
                <span className="btn-spinner" aria-hidden="true" /> Starting Run...
              </>
            ) : (
              '⚡ Run Agent'
            )}
          </button>
        </div>
      </div>

      {/* Live Run Execution Section */}
      {runState && (
        <div className="agent-run-section animate-fade-up">
          <div className="run-header-card">
            <div className="run-header-meta">
              <span className="eyebrow-tag">RUN ID: {runState.run_id}</span>
              <div className="run-status-badge-container">
                <span className={`run-status-badge status-${runState.status}`}>
                  {runState.status === 'running' && <span className="status-pulse-dot" />}
                  {runState.status.toUpperCase().replace(/_/g, ' ')}
                </span>
              </div>
            </div>
          </div>

          {/* Pending Human Approval Card (Prominent Glowing Card) */}
          {runState.pending_approval && (
            <div className="approval-card animate-pulse-glow">
              <div className="approval-card-header">
                <span className="approval-warning-icon">⚠️</span>
                <div>
                  <h3 className="approval-card-title">Human Supervisor Approval Required</h3>
                  <p className="approval-card-subtitle">
                    The agent requests permission to execute a write action on external storage.
                  </p>
                </div>
              </div>

              <div className="approval-details">
                <div className="approval-field">
                  <span className="approval-label">Target Tool:</span>
                  <code className="approval-code-tag">{runState.pending_approval.tool}</code>
                </div>
                <div className="approval-field">
                  <span className="approval-label">Agent Reason:</span>
                  <p className="approval-reason-text">{runState.pending_approval.reason}</p>
                </div>
                <div className="approval-field">
                  <span className="approval-label">Tool Arguments:</span>
                  <pre className="approval-args-json">
                    {JSON.stringify(runState.pending_approval.args, null, 2)}
                  </pre>
                </div>
              </div>

              <div className="approval-actions">
                <button
                  type="button"
                  className="btn-solid shine-effect approve-btn"
                  onClick={() => handleApproveDecision(true)}
                  disabled={isApproving}
                >
                  {isApproving ? 'Submitting...' : '✅ Approve Action'}
                </button>
                <button
                  type="button"
                  className="btn-ghost shine-effect reject-btn"
                  onClick={() => handleApproveDecision(false)}
                  disabled={isApproving}
                >
                  {isApproving ? 'Submitting...' : '❌ Reject Action'}
                </button>
              </div>
            </div>
          )}

          {/* Final Result Summary Card (Appears when run concludes) */}
          {isTerminal && (
            <div className={`final-result-card result-${runState.status}`}>
              <div className="result-card-header">
                <span className="result-icon">{runState.status === 'completed' ? '🎉' : '🛑'}</span>
                <div>
                  <h3 className="result-title">
                    Run Concluded — {runState.status.toUpperCase().replace(/_/g, ' ')}
                  </h3>
                  {verifiedItemId && (
                    <div className="verified-badge">
                      <span>✓ Verified Backlog Item:</span> <code>{verifiedItemId}</code>
                    </div>
                  )}
                </div>
              </div>

              {runState.final_answer && (
                <div className="final-answer-container">
                  <span className="eyebrow-tag">FINAL ANSWER</span>
                  <p className="final-answer-text">{runState.final_answer}</p>
                </div>
              )}
            </div>
          )}

          {/* Live Timeline Event Trace */}
          <div className="timeline-container">
            <span className="eyebrow-tag timeline-eyebrow">LIVE EVENT TIMELINE TRACE</span>

            {(!runState.trace || runState.trace.length === 0) ? (
              <div className="timeline-empty">
                <span className="spinner" />
                <p>Initializing agent planner loop...</p>
              </div>
            ) : (
              <div className="timeline-list">
                {runState.trace.map((evt, idx) => {
                  const meta = getEventMeta(evt)
                  const timestamp = formatTime(evt.timestamp)

                  return (
                    <div key={idx} className={`timeline-item ${meta.cardClass}`}>
                      <div className="timeline-node">
                        <span className="node-icon">{meta.icon}</span>
                      </div>

                      <div className="timeline-content">
                        <div className="timeline-item-header">
                          <span className="item-title">{meta.title}</span>
                          {timestamp && <span className="item-timestamp">{timestamp}</span>}
                        </div>

                        {/* Event Specific Render Details */}
                        {evt.event_type === 'goal_received' && (
                          <p className="evt-detail-text">&quot;{evt.goal}&quot;</p>
                        )}

                        {evt.event_type === 'decision' && (
                          <div className="decision-box">
                            <div className="decision-row">
                              <span className="dec-label">Action:</span> <code>{evt.decision?.action}</code>
                              {evt.decision?.tool && (
                                <>
                                  <span className="dec-label">Tool:</span> <code>{evt.decision?.tool}</code>
                                </>
                              )}
                            </div>
                            {evt.decision?.reason && (
                              <p className="dec-reason">&quot;{evt.decision.reason}&quot;</p>
                            )}
                          </div>
                        )}

                        {evt.event_type === 'tool_call' && (
                          <div className="tool-call-box">
                            <span className="tool-name">Tool: {evt.tool}</span>
                            {evt.attempt > 1 && <span className="attempt-badge">Attempt #{evt.attempt}</span>}
                            {evt.args && Object.keys(evt.args).length > 0 && (
                              <pre className="args-snippet">{JSON.stringify(evt.args, null, 2)}</pre>
                            )}
                          </div>
                        )}

                        {evt.event_type === 'tool_result' && (
                          <div className="tool-result-box">
                            <span className="result-status">
                              {evt.result?.ok ? 'Success' : `Error (${evt.result?.error_type || 'failed'})`}
                            </span>
                            {evt.result?.error && <p className="error-msg">{evt.result.error}</p>}
                            {evt.result?.data && (
                              <div className="result-data-preview">
                                <pre className="data-json">
                                  {JSON.stringify(evt.result.data, null, 2)}
                                </pre>
                              </div>
                            )}
                          </div>
                        )}

                        {evt.event_type === 'retry' && (
                          <div className="retry-box">
                            <p>
                              ⚠️ Transient error on tool <code>{evt.tool}</code>. Waiting{' '}
                              <strong>{evt.wait_seconds}s</strong> before retry attempt #{evt.attempt + 1}.
                            </p>
                          </div>
                        )}

                        {evt.event_type === 'finish' && (
                          <div className="finish-box">
                            <p className="finish-answer">{evt.final_answer}</p>
                          </div>
                        )}

                        {evt.event_type === 'halted' && (
                          <div className="halted-box">
                            <p className="halted-reason">{evt.reason}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default AgentView
