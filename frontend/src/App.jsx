
import { useCallback, useEffect, useState } from 'react'
import api from './api'
import './App.css'

const navigation = [
  { label: 'Overview', icon: '▦' },
  { label: 'Production Batches', icon: '▤' },
  { label: 'Quality Inspections', icon: '✓' },
  { label: 'Workflow Tracking', icon: '⇄' },
  { label: 'Supervisor Reviews', icon: '◎' },
]

const workflowStages = [
  'Raw Material',
  'Machining',
  'Heat Treatment',
  'Grinding',
  'Final Inspection',
  'Packing',
  'Dispatch',
]

function App() {
  const [activePage, setActivePage] = useState('Overview')
  const [search, setSearch] = useState('')
  const [batchesData, setBatchesData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [inspectionsData, setInspectionsData] = useState([])
  const [inspectionsLoading, setInspectionsLoading] = useState(true)
  const [inspectionsError, setInspectionsError] = useState('')
  const [measurementValues, setMeasurementValues] = useState({})
  const [measurementRemarks, setMeasurementRemarks] = useState({})
  const [savingMeasurementId, setSavingMeasurementId] = useState(null)
  const [reviewingId, setReviewingId] = useState(null)
  const [reviewMessage, setReviewMessage] = useState('')
  const [reviewError, setReviewError] = useState('')

  const fetchBatches = useCallback(async () => {
    try {
      setLoading(true)
      setError('')

      const response = await api.get('/production/batches/')
      setBatchesData(
        Array.isArray(response.data)
          ? response.data
          : response.data.results || [],
      )
    } catch (err) {
      console.error('Failed to fetch batches:', err)
      setError(
        err.response?.status === 401 || err.response?.status === 403
          ? 'Authentication required. Please log in to the backend.'
          : 'Unable to load production batches. Check the backend server.',
      )
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchInspections = useCallback(async () => {
    try {
      setInspectionsLoading(true)
      setInspectionsError('')

      const response = await api.get('/quality/inspections/')
      setInspectionsData(
        Array.isArray(response.data)
          ? response.data
          : response.data.results || [],
      )
    } catch (err) {
      console.error('Failed to fetch inspections:', err)
      setInspectionsError(
        err.response?.status === 401 || err.response?.status === 403
          ? 'Authentication required to view inspections.'
          : 'Unable to load inspection data.',
      )
    } finally {
      setInspectionsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchBatches()
    fetchInspections()
  }, [fetchBatches, fetchInspections])

  const handleReview = async (inspection, decision) => {
    if (inspection.result === 'PENDING') {
      setReviewError(
        `Inspection #${inspection.id} has no recorded measurement. Record its measurement before reviewing it.`,
      )
      setReviewMessage('')
      return
    }

    if (
      decision === 'APPROVED' &&
      inspection.result !== 'PASS'
    ) {
      setReviewError(
        `Inspection #${inspection.id} failed quality checks and cannot be approved.`,
      )
      setReviewMessage('')
      return
    }

    if (inspection.approval_status !== 'PENDING_REVIEW') {
      setReviewError(
        `Inspection #${inspection.id} has already been reviewed.`,
      )
      setReviewMessage('')
      return
    }

    const action = decision === 'APPROVED' ? 'approve' : 'reject'

    if (
      !window.confirm(
        `Are you sure you want to ${action} inspection #${inspection.id}?`,
      )
    ) {
      return
    }

    try {
      setReviewingId(inspection.id)
      setReviewMessage('')
      setReviewError('')

      const response = await api.post(
        `/workflow/inspections/${inspection.id}/review/`,
        { decision },
      )

      setReviewMessage(
        response.data.message || `Inspection #${inspection.id} reviewed successfully.`,
      )

      await Promise.all([fetchInspections(), fetchBatches()])
    } catch (err) {
      console.error('Failed to review inspection:', err)

      const data = err.response?.data
      const message =
        data?.error ||
        (typeof data === 'string' ? data : '') ||
        (err.response?.status === 401
          ? 'Please log in before reviewing inspections.'
          : err.response?.status === 403
            ? 'Permission denied. Only a Quality Supervisor or superuser can review inspections.'
            : 'Could not submit the review. Check the backend and try again.')

      setReviewError(message)
    } finally {
      setReviewingId(null)
    }
  }

const handleRecordMeasurement = async (inspection) => {
  const rawValue = measurementValues[inspection.id]

  if (rawValue === undefined || String(rawValue).trim() === '') {
    setReviewError('Please enter a measurement value.')
    setReviewMessage('')
    return
  }

  try {
    setSavingMeasurementId(inspection.id)
    setReviewError('')
    setReviewMessage('')

    const response = await api.post(
      `/quality/inspections/${inspection.id}/measurement/`,
      {
        measured_value: rawValue,
        inspector_remarks: measurementRemarks[inspection.id] || '',
      },
    )

    setReviewMessage(
      response.data.message || 'Measurement recorded successfully.',
    )

    setMeasurementValues((previous) => ({
      ...previous,
      [inspection.id]: '',
    }))

    setMeasurementRemarks((previous) => ({
      ...previous,
      [inspection.id]: '',
    }))

    await Promise.all([fetchInspections(), fetchBatches()])
  } catch (err) {
    console.error('Failed to record measurement:', err)

    setReviewError(
      err.response?.data?.error ||
        'Could not record the measurement. Please try again.',
    )
  } finally {
    setSavingMeasurementId(null)
  }
}

  const batches = batchesData.filter((batch) =>
    `${batch.batch_number} ${batch.part_number} ${batch.current_stage}`
      .toLowerCase()
      .includes(search.toLowerCase()),
  )

  const inProductionCount = batchesData.filter(
    (batch) => batch.status === 'IN_PROGRESS',
  ).length

  const onHoldCount = batchesData.filter(
    (batch) => batch.status === 'ON_HOLD',
  ).length

  const passedInspections = inspectionsData.filter(
    (inspection) => inspection.result === 'PASS',
  ).length

  const failedInspections = inspectionsData.filter(
    (inspection) => inspection.result === 'FAIL',
  ).length

  const pendingMeasurements = inspectionsData.filter(
    (inspection) => inspection.result === 'PENDING',
  ).length

  const pendingReviews = inspectionsData.filter(
    (inspection) =>
      inspection.approval_status === 'PENDING_REVIEW',
  )

  const formatLabel = (value = '') =>
    value
      .toLowerCase()
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')

  const pageDescriptions = {
    'Production Batches':
      'Manage production batches and monitor manufacturing progress.',
    'Quality Inspections':
      'Review recorded measurements, tolerance limits and quality results.',
    'Workflow Tracking':
      'Track the manufacturing stages for production batches.',
    'Supervisor Reviews':
      'Review inspections and submit authorized approval decisions.',
  }

  const renderBatchTable = () => (
    <>
      {error && (
        <div className="empty-state" role="alert">
          {error}
        </div>
      )}

      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Batch number</th>
              <th>Part number</th>
              <th>Quantity</th>
              <th>Current stage</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="5" className="empty-state">
                  Loading production batches...
                </td>
              </tr>
            ) : (
              <>
                {batches.map((batch) => (
                  <tr key={batch.id}>
                    <td>
                      <strong className="batch-number">
                        {batch.batch_number}
                      </strong>
                    </td>
                    <td>{batch.part_number}</td>
                    <td>{batch.quantity} units</td>
                    <td>
                      <span className="stage-label">
                        {formatLabel(batch.current_stage)}
                      </span>
                    </td>
                    <td>
                      <span
                        className={`status-pill ${
                          batch.status === 'ON_HOLD' ||
                          batch.status === 'REJECTED'
                            ? 'hold'
                            : 'progress'
                        }`}
                      >
                        <span className="status-dot" />
                        {formatLabel(batch.status)}
                      </span>
                    </td>
                  </tr>
                ))}

                {batches.length === 0 && !error && (
                  <tr>
                    <td colSpan="5" className="empty-state">
                      {batchesData.length === 0
                        ? 'No production batches found.'
                        : 'No batches match your search.'}
                    </td>
                  </tr>
                )}
              </>
            )}
          </tbody>
        </table>
      </div>

      <div className="table-footer">
        <span>
          Showing {batches.length} of {batchesData.length} batches
        </span>
        <span>
          {loading ? 'Fetching data...' : 'Django API connection'}
        </span>
      </div>
    </>
  )

  const renderInspectionTable = (reviewsOnly = false) => {
    const displayedInspections = reviewsOnly
      ? pendingReviews
      : inspectionsData

    if (inspectionsLoading) {
      return (
        <div className="empty-state">
          Loading quality inspection data...
        </div>
      )
    }

    if (inspectionsError) {
      return (
        <div className="empty-state" role="alert">
          {inspectionsError}
        </div>
      )
    }

    if (displayedInspections.length === 0) {
      return (
        <div className="empty-state">
          {reviewsOnly
            ? 'No inspections are awaiting supervisor review.'
            : 'No quality inspections found.'}
        </div>
      )
    }

    return (
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Inspection</th>
              <th>Batch ID</th>
              <th>Stage</th>
              <th>Parameter</th>
              <th>Measured value</th>
              <th>Result</th>
              <th>Approval</th>
              {reviewsOnly && <th>Review action</th>}
            </tr>
          </thead>
          <tbody>
            {displayedInspections.map((inspection) => {
              const isPendingMeasurement =
                inspection.result === 'PENDING'
              const isFailed = inspection.result === 'FAIL'
              const isAlreadyReviewed =
                inspection.approval_status !== 'PENDING_REVIEW'
              const isReviewing = reviewingId === inspection.id

              return (
                <tr key={inspection.id}>
                  <td>#{inspection.id}</td>
                  <td>{inspection.batch}</td>
                  <td>{formatLabel(inspection.stage)}</td>
                  <td>{inspection.parameter_name}</td>

                  <td>
                    {inspection.measured_value ?? 'Not recorded'}

                    {inspection.result === 'PENDING' &&
                      inspection.measured_value == null && (
                        <div className="measurement-form">
                          <input
                            type="number"
                            step="0.001"
                            placeholder="Enter measurement"
                            aria-label={`Measurement for inspection ${inspection.id}`}
                            value={measurementValues[inspection.id] ?? ''}
                            onChange={(event) =>
                              setMeasurementValues((previous) => ({
                                ...previous,
                                [inspection.id]: event.target.value,
                              }))
                            }
                          />

                          <input
                            type="text"
                            placeholder="Inspector remarks (optional)"
                            aria-label={`Remarks for inspection ${inspection.id}`}
                            value={measurementRemarks[inspection.id] ?? ''}
                            onChange={(event) =>
                              setMeasurementRemarks((previous) => ({
                                ...previous,
                                [inspection.id]: event.target.value,
                              }))
                            }
                          />

                          <button
                            type="button"
                            disabled={savingMeasurementId !== null}
                            onClick={() =>
                              handleRecordMeasurement(inspection)
                            }
                          >
                            {savingMeasurementId === inspection.id
                              ? 'Saving...'
                              : 'Record Measurement'}
                          </button>
                        </div>
                      )}
                  </td>

                  <td>{formatLabel(inspection.result)}</td>
                  <td>{formatLabel(inspection.approval_status)}</td>

                  {reviewsOnly && (
                    <td>
                      {isAlreadyReviewed ? (
                        <span>{formatLabel(inspection.approval_status)}</span>
                      ) : isPendingMeasurement ? (
                        <span title="Record a measurement before reviewing">
                          Measurement required
                        </span>
                      ) : (
                        <div className="review-actions">
                          {inspection.result === 'PASS' && (
                            <button
                              type="button"
                              disabled={reviewingId !== null}
                              onClick={() =>
                                handleReview(inspection, 'APPROVED')
                              }
                            >
                              {isReviewing ? 'Saving...' : 'Approve'}
                            </button>
                          )}

                          <button
                            type="button"
                            disabled={reviewingId !== null}
                            onClick={() =>
                              handleReview(inspection, 'REJECTED')
                            }
                          >
                            {isReviewing ? 'Saving...' : 'Reject'}
                          </button>

                          {isFailed && (
                            <span title="Failed measurements cannot be approved">
                              Failed
                            </span>
                          )}
                        </div>
                      )}
                    </td>
                  )}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    )
  }

  const renderWorkflow = () => (
    <div className="workflow-list">
      {workflowStages.map((stage, index) => (
        <div className="workflow-step" key={stage}>
          <span className="workflow-number">{index + 1}</span>
          <span>{stage}</span>
          <span className="workflow-arrow">→</span>
        </div>
      ))}
    </div>
  )

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">Z</div>
          <div>
            <h2>ZAPUZA</h2>
            <span>FACTORY OPERATIONS</span>
          </div>
        </div>

        <div className="workspace-label">WORKSPACE</div>

        <nav className="navigation">
          {navigation.map((item) => (
            <button
              key={item.label}
              className={`nav-item ${
                activePage === item.label ? 'active' : ''
              }`}
              onClick={() => setActivePage(item.label)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="system-status">
            <span className="status-dot" />
            <div>
              <strong>System operational</strong>
              <span>Factory quality platform</span>
            </div>
          </div>

          <div className="user-profile">
            <div className="avatar">S</div>
            <div>
              <strong>System Operator</strong>
              <span>Operations team</span>
            </div>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <span className="breadcrumb">Workspace / </span>
            <strong>{activePage}</strong>
          </div>

          <div className="topbar-right">
            <span className="environment">
              <span className="status-dot" />
              Development
            </span>
            <div className="avatar">S</div>
          </div>
        </header>

        <div className="page-content">
          {activePage === 'Overview' ? (
            <>
              <section className="welcome-section">
                <div>
                  <span className="eyebrow">
                    FACTORY MANAGEMENT SYSTEM
                  </span>
                  <h1>Overview</h1>
                  <p>
                    Monitor production progress and quality operations
                    in one place.
                  </p>
                </div>

                <div className="date-label">
                  <span>⌁</span> Production control center
                </div>
              </section>

              <section className="metrics-grid">
                <article className="metric-card">
                  <div className="metric-heading">
                    <span>Total batches</span>
                    <span className="metric-icon blue">▤</span>
                  </div>
                  <strong className="metric-number">
                    {batchesData.length}
                  </strong>
                  <span className="metric-footnote">
                    Batches currently recorded
                  </span>
                </article>

                <article className="metric-card">
                  <div className="metric-heading">
                    <span>In production</span>
                    <span className="metric-icon purple">↗</span>
                  </div>
                  <strong className="metric-number">
                    {inProductionCount}
                  </strong>
                  <span className="metric-footnote">
                    Currently in progress
                  </span>
                </article>

                <article className="metric-card">
                  <div className="metric-heading">
                    <span>Quality failures</span>
                    <span className="metric-icon red">!</span>
                  </div>
                  <strong className="metric-number">
                    {failedInspections}
                  </strong>
                  <span className="metric-footnote">
                    Failed quality inspections
                  </span>
                </article>

                <article className="metric-card">
                  <div className="metric-heading">
                    <span>On hold</span>
                    <span className="metric-icon amber">Ⅱ</span>
                  </div>
                  <strong className="metric-number">
                    {onHoldCount}
                  </strong>
                  <span className="metric-footnote">
                    Batches on hold
                  </span>
                </article>
              </section>

              <section className="content-card">
                <div className="card-header">
                  <div>
                    <h2>Production batches</h2>
                    <p>
                      Track batch status and current manufacturing stages.
                    </p>
                  </div>

                  <label className="search-box">
                    <span>⌕</span>
                    <input
                      type="search"
                      placeholder="Search batches..."
                      value={search}
                      onChange={(event) => setSearch(event.target.value)}
                    />
                  </label>
                </div>

                {renderBatchTable()}
              </section>

              <section className="bottom-grid">
                <article className="content-card activity-card">
                  <div className="card-header">
                    <div>
                      <h2>Quality control</h2>
                      <p>Inspection summary</p>
                    </div>
                    <span className="metric-icon blue">✓</span>
                  </div>

                  <div className="quality-row">
                    <div className="quality-symbol pass">✓</div>
                    <div className="quality-copy">
                      <strong>Passed inspections</strong>
                      <span>Measurements within specified limits</span>
                    </div>
                    <strong>{passedInspections}</strong>
                  </div>

                  <div className="quality-row">
                    <div className="quality-symbol fail">!</div>
                    <div className="quality-copy">
                      <strong>Failed inspections</strong>
                      <span>Require investigation and review</span>
                    </div>
                    <strong>{failedInspections}</strong>
                  </div>

                  <div className="quality-row">
                    <div className="quality-symbol pending">…</div>
                    <div className="quality-copy">
                      <strong>Pending measurements</strong>
                      <span>Awaiting recorded measurement values</span>
                    </div>
                    <strong>{pendingMeasurements}</strong>
                  </div>

                  <p className="metric-footnote">
                    Inspection statistics from the Django API.
                  </p>
                </article>

                <article className="content-card workflow-card">
                  <div className="card-header">
                    <div>
                      <h2>Manufacturing workflow</h2>
                      <p>Standard production stages</p>
                    </div>
                  </div>
                  {renderWorkflow()}
                </article>
              </section>
            </>
          ) : (
            <>
              <section className="welcome-section">
                <div>
                  <span className="eyebrow">
                    FACTORY MANAGEMENT SYSTEM
                  </span>
                  <h1>{activePage}</h1>
                  <p>{pageDescriptions[activePage]}</p>
                </div>
              </section>

              {reviewMessage && (
                <div className="empty-state" role="status">
                  {reviewMessage}
                </div>
              )}

              {reviewError && (
                <div className="empty-state" role="alert">
                  {reviewError}
                </div>
              )}

              {activePage === 'Production Batches' && (
                <section className="content-card">
                  <div className="card-header">
                    <div>
                      <h2>Production batches</h2>
                      <p>
                        Live batch records from the Django backend.
                      </p>
                    </div>

                    <label className="search-box">
                      <span>⌕</span>
                      <input
                        type="search"
                        placeholder="Search batches..."
                        value={search}
                        onChange={(event) => setSearch(event.target.value)}
                      />
                    </label>
                  </div>

                  {renderBatchTable()}
                </section>
              )}

              {activePage === 'Quality Inspections' && (
                <section className="content-card">
                  <div className="card-header">
                    <div>
                      <h2>Quality inspection records</h2>
                      <p>
                        Measurements, results and approval status.
                      </p>
                    </div>
                  </div>
                  {renderInspectionTable()}
                </section>
              )}

              {activePage === 'Workflow Tracking' && (
                <section className="content-card workflow-card">
                  <div className="card-header">
                    <div>
                      <h2>Manufacturing stages</h2>
                      <p>
                        Standard order of production stages.
                      </p>
                    </div>
                  </div>
                  {renderWorkflow()}

                  <div className="table-wrapper">
                    <table>
                      <thead>
                        <tr>
                          <th>Batch</th>
                          <th>Part number</th>
                          <th>Current stage</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {batchesData.map((batch) => (
                          <tr key={batch.id}>
                            <td>{batch.batch_number}</td>
                            <td>{batch.part_number}</td>
                            <td>{formatLabel(batch.current_stage)}</td>
                            <td>{formatLabel(batch.status)}</td>
                          </tr>
                        ))}
                        {!loading && batchesData.length === 0 && (
                          <tr>
                            <td colSpan="4" className="empty-state">
                              {error || 'No production batches found.'}
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </section>
              )}

              {activePage === 'Supervisor Reviews' && (
                <section className="content-card">
                  <div className="card-header">
                    <div>
                      <h2>Pending supervisor reviews</h2>
                      <p>
                        Approve passing inspections or reject inspections
                        that require corrective action.
                      </p>
                    </div>
                  </div>
                  {renderInspectionTable(true)}
                </section>
              )}

              <footer className="page-footer">
                <span>
                  ZAPUZA · Factory Operations &amp; Quality Control
                </span>
                <span>React + Django</span>
              </footer>
            </>
          )}
        </div>
      </main>
    </div>
  )
}

export default App
