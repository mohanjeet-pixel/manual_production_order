import { useState, useEffect } from 'react'
import { api } from '../api.js'
import StatusBadge from '../components/StatusBadge.jsx'
import { fmtINR } from '../utils.js'

function StatCard({ title, value, hint, variant }) {
  return (
    <div className={`stat-card${variant ? ` ${variant}` : ''}`}>
      <div className="stat-label">{title}</div>
      <div className="stat-number">{value}</div>
      <div className="stat-hint">{hint}</div>
    </div>
  )
}

export default function Dashboard() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getOrders()
      .then(setOrders)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="page-body"><div className="loading">Loading...</div></div>

  const total    = orders.length
  const pending  = orders.filter(o => o.Status === 'PENDING').length
  const approved = orders.filter(o => o.Status === 'APPROVED').length
  const rejected = orders.filter(o => o.Status === 'REJECTED').length
  const totalValue = orders.reduce((sum, o) => sum + (parseFloat(o.Value) || 0), 0)
  const recent = orders.slice(0, 5)

  return (
    <div className="page-body">
      <div className="page-title">Dashboard</div>
      {error && <div className="msg-error">{error}</div>}

      <div className="stats-row">
        <StatCard title="Total Orders"  value={total}    hint="all time" />
        <StatCard title="Pending"       value={pending}  hint="awaiting approval" variant="pending" />
        <StatCard title="Approved"      value={approved} hint="orders approved"   variant="approved" />
        <StatCard title="Rejected"      value={rejected} hint="orders rejected"   variant="rejected" />
      </div>

      <div className="value-banner">
        <div>
          <div className="value-banner-label">Total Order Value</div>
          <div className="value-banner-amount">{fmtINR(totalValue)}</div>
        </div>
        <span style={{ fontSize: 36, opacity: 0.5 }}>&#128200;</span>
      </div>

      <div className="card">
        <div className="card-header">
          <span>Recent Orders</span>
          <span className="card-header-sub">Last 5 orders</span>
        </div>
        <div className="card-body">
          <RecentTable orders={recent} />
        </div>
      </div>
    </div>
  )
}

function RecentTable({ orders }) {
  if (!orders.length) return <div className="empty">No orders yet.</div>
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>ID</th><th>Plant</th><th>Part No</th>
            <th>Qty</th><th>Value</th><th>Status</th><th>Date</th>
          </tr>
        </thead>
        <tbody>
          {orders.map(o => (
            <tr key={o.ID}>
              <td>{o.ID}</td>
              <td>{o.Plant}</td>
              <td>{o['Part No']}</td>
              <td>{o.Quantity}</td>
              <td>{fmtINR(o.Value)}</td>
              <td><StatusBadge status={o.Status} /></td>
              <td>{o.created_at}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
