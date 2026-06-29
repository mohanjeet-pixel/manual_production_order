import { useState, useEffect, useRef } from 'react'
import { api } from '../api.js'
import StatusBadge from '../components/StatusBadge.jsx'
import { fmtINR } from '../utils.js'

// Simulated steps while SAP background task is running
const SAP_STEPS = [
  { until: 8,   label: 'Connecting to SAP…' },
  { until: 25,  label: 'Validating material & plant…' },
  { until: 70,  label: 'Scheduling production…' },
  { until: 140, label: 'Releasing order…' },
  { until: 9999, label: 'Saving confirmation…' },
]

function elapsedSecs(approvedAt) {
  if (!approvedAt) return 0
  return Math.max(0, (Date.now() - new Date(approvedAt).getTime()) / 1000)
}

function currentStep(approvedAt) {
  const secs = elapsedSecs(approvedAt)
  return (SAP_STEPS.find(s => secs < s.until) || SAP_STEPS.at(-1)).label
}

// Parse JSON messages string → extract meaningful texts
function parseMessages(raw) {
  try {
    const list = typeof raw === 'string' ? JSON.parse(raw) : (raw || [])
    return list.map(m => m.text || '').filter(Boolean)
  } catch {
    return []
  }
}

function SapCell({ order }) {
  const [stepLabel, setStepLabel] = useState(() => currentStep(order['Approved At']))

  // Tick the step label every 2s while waiting for SAP
  useEffect(() => {
    if (order.Status !== 'APPROVED' || order.sap_status) return
    const t = setInterval(() => setStepLabel(currentStep(order['Approved At'])), 2000)
    return () => clearInterval(t)
  }, [order.sap_status, order['Approved At']])

  if (order.Status !== 'APPROVED') {
    return <span style={{ color: '#94a3b8' }}>—</span>
  }

  // ── Still running ──────────────────────────────────────────
  if (!order.sap_status) {
    const stepIndex = SAP_STEPS.findIndex(s => s.label === stepLabel)
    const progress  = Math.min(100, Math.round(((stepIndex + 1) / SAP_STEPS.length) * 100))

    return (
      <div className="sap-cell-loading">
        <div className="sap-cell-header">
          <span className="sap-spinner" />
          <span className="sap-cell-title">Submitting to SAP</span>
        </div>

        <div className="sap-progress-bar-wrap">
          <div className="sap-progress-bar" style={{ width: `${progress}%` }} />
        </div>

        <div className="sap-steps">
          {SAP_STEPS.slice(0, -1).map((s, i) => {
            const done    = i < stepIndex
            const active  = i === stepIndex
            return (
              <div key={i} className={`sap-step ${done ? 'done' : active ? 'active' : 'waiting'}`}>
                <span className="sap-step-dot" />
                <span className="sap-step-label">{s.label}</span>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  // ── Success ────────────────────────────────────────────────
  if (order.sap_status === 'SUCCESS') {
    const msgs   = parseMessages(order.sap_messages)
    const lastMsg = order.sap_order_no || msgs.at(-1) || 'Submitted'

    return (
      <div className="sap-cell-done sap-cell-success">
        <div className="sap-cell-header">
          <span className="sap-icon-success">✓</span>
          <span className="sap-cell-title">SAP Submitted</span>
        </div>
        <div className="sap-result-msg">{lastMsg}</div>
        {msgs.length > 1 && (
          <details className="sap-messages-detail">
            <summary>All messages ({msgs.length})</summary>
            <ul>
              {msgs.map((m, i) => <li key={i}>{m}</li>)}
            </ul>
          </details>
        )}
      </div>
    )
  }

  // ── Failed ─────────────────────────────────────────────────
  const msgs    = parseMessages(order.sap_messages)
  const errText = msgs.at(-1) || order.sap_error || 'SAP submission failed'

  return (
    <div className="sap-cell-done sap-cell-failed">
      <div className="sap-cell-header">
        <span className="sap-icon-fail">✗</span>
        <span className="sap-cell-title">SAP Failed</span>
      </div>
      <div className="sap-result-msg">{errText}</div>
    </div>
  )
}

export default function History() {
  const [orders, setOrders]   = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState('')
  const [search, setSearch]   = useState('')
  const [filter, setFilter]   = useState('ALL')
  const pollRef               = useRef(null)

  function loadOrders() {
    return api.getOrders()
      .then(data => setOrders(Array.isArray(data) ? data : (data.data || [])))
      .catch(err => setError(err.message))
  }

  useEffect(() => { loadOrders().finally(() => setLoading(false)) }, [])

  useEffect(() => {
    const hasPending = orders.some(o => o.Status === 'APPROVED' && !o.sap_status)
    clearInterval(pollRef.current)
    if (hasPending) pollRef.current = setInterval(loadOrders, 5000)
    return () => clearInterval(pollRef.current)
  }, [orders])

  const filtered = orders.filter(o => {
    const matchStatus = filter === 'ALL' || o.Status === filter
    const matchSearch = !search || Object.values(o)
      .some(v => String(v).toLowerCase().includes(search.toLowerCase()))
    return matchStatus && matchSearch
  })

  if (loading) return <div className="page-body"><div className="loading">Loading...</div></div>

  return (
    <div className="page-body">
      <div className="page-title">Order History</div>
      {error && <div className="msg-error">{error}</div>}

      <div className="card">
        <div className="card-header">
          <span>All Orders</span>
          <span className="card-header-sub">{filtered.length} records</span>
        </div>
        <div className="card-body">

          <div className="history-toolbar">
            <input
              className="field-input"
              placeholder="Search..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{ maxWidth: 260 }}
            />
            <div className="filter-tabs">
              {['ALL', 'PENDING', 'APPROVED', 'REJECTED'].map(s => (
                <button
                  key={s}
                  className={`filter-btn${filter === s ? ' active' : ''}`}
                  onClick={() => setFilter(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th><th>Plant</th><th>Part No</th><th>Qty</th>
                  <th>Unit Price</th><th>Value</th><th>Status</th>
                  <th style={{ minWidth: 240 }}>SAP Status</th>
                  <th>Batch</th><th>Date</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(o => (
                  <tr key={o.ID}>
                    <td>{o.ID}</td>
                    <td>{o.Plant}</td>
                    <td>{o['Part No']}</td>
                    <td>{o.Quantity}</td>
                    <td>{fmtINR(o['Unit Price'])}</td>
                    <td>{fmtINR(o.Value)}</td>
                    <td><StatusBadge status={o.Status} /></td>
                    <td style={{ verticalAlign: 'top', padding: '10px 8px' }}>
                      <SapCell order={o} />
                    </td>
                    <td>{o.batch_id || '—'}</td>
                    <td>{o.created_at || '—'}</td>
                  </tr>
                ))}
                {!filtered.length && (
                  <tr><td colSpan={10} className="empty">No orders found.</td></tr>
                )}
              </tbody>
            </table>
          </div>

        </div>
      </div>
    </div>
  )
}
