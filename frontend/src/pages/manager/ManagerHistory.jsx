import { useState, useEffect } from 'react'
import { api } from '../../api.js'
import StatusBadge from '../../components/StatusBadge.jsx'

const fmt = v => `₹${Number(v).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`

const FILTERS = [
  { label: 'All',      value: null },
  { label: 'Pending',  value: 'PENDING' },
  { label: 'Approved', value: 'APPROVED' },
  { label: 'Rejected', value: 'REJECTED' },
]

export default function ManagerHistory() {
  const [orders, setOrders]         = useState([])
  const [loading, setLoading]       = useState(true)
  const [filter, setFilter]         = useState(null)
  const [error, setError]           = useState('')
  const [msg, setMsg]               = useState('')
  const [reapproving, setReapproving] = useState(null)

  useEffect(() => { loadHistory() }, [filter])

  async function loadHistory() {
    setLoading(true)
    setError('')
    try {
      const res = await api.getApprovalHistory(filter)
      setOrders(res.data || [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleReApprove(token) {
    if (!window.confirm('Re-approve this rejected order? This can only be done once.')) return
    setReapproving(token)
    setError('')
    try {
      await api.reApproveOrder(token)
      setMsg('Order re-approved and submitted to SAP')
      setTimeout(() => setMsg(''), 4000)
      loadHistory()
    } catch (e) {
      setError(e.message)
    } finally {
      setReapproving(null)
    }
  }

  return (
    <div className="page-body">
      <h1 className="page-title">Approval History</h1>

      {msg   && <div className="msg-success">{msg}</div>}
      {error && <div className="msg-error">{error}</div>}

      <div className="history-toolbar">
        <div className="filter-tabs">
          {FILTERS.map(f => (
            <button
              key={String(f.value)}
              className={`filter-btn${filter === f.value ? ' active' : ''}`}
              onClick={() => setFilter(f.value)}
            >
              {f.label}
            </button>
          ))}
        </div>
        <span style={{ fontSize: 13, color: '#94a3b8' }}>{orders.length} records</span>
      </div>

      <div className="card">
        {loading ? (
          <div className="loading">Loading…</div>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Employee</th>
                  <th>Plant</th>
                  <th>Part No</th>
                  <th>Qty</th>
                  <th>Unit Price</th>
                  <th>Value</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {orders.length === 0 && (
                  <tr><td colSpan={10} className="empty">No orders found</td></tr>
                )}
                {orders.map(o => (
                  <tr key={o.id}>
                    <td>{o.id}</td>
                    <td><strong>{o.employee_id}</strong></td>
                    <td>{o.plant}</td>
                    <td>{o.part_no}</td>
                    <td>{o.quantity}</td>
                    <td>{fmt(o.unit_price)}</td>
                    <td><strong style={{ color: '#1a3c5e' }}>{fmt(o.value)}</strong></td>
                    <td><StatusBadge status={o.status} /></td>
                    <td>{o.created_at}</td>
                    <td>
                      {o.status === 'REJECTED' && (
                        <button
                          className="btn-action-sm btn-action-blue"
                          disabled={reapproving === o.token}
                          onClick={() => handleReApprove(o.token)}
                        >
                          {reapproving === o.token ? '…' : 'Re-approve'}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
