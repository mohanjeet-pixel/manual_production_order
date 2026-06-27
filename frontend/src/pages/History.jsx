import { useState, useEffect } from 'react'
import { api } from '../api.js'
import StatusBadge from '../components/StatusBadge.jsx'
import { fmtINR } from '../utils.js'

export default function History() {
  const [orders, setOrders]   = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState('')
  const [search, setSearch]   = useState('')
  const [filter, setFilter]   = useState('ALL')

  useEffect(() => {
    api.getOrders()
      .then(setOrders)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

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
                  <th>Batch</th><th>Approved By</th><th>Approved At</th>
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
                    <td>{o.batch_id || '—'}</td>
                    <td>{o['Approved By'] || '—'}</td>
                    <td>{o['Approved At'] || '—'}</td>
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
