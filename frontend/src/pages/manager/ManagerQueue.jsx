import { useState, useEffect } from 'react'
import { api } from '../../api.js'
import { fmtINR } from '../../utils.js'

export default function ManagerQueue() {
  const [orders,  setOrders]  = useState([])
  const [batches, setBatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState('')
  const [msg,     setMsg]     = useState('')
  const [acting,  setActing]  = useState(null)

  useEffect(() => { loadAll() }, [])

  async function loadAll() {
    setLoading(true)
    setError('')
    try {
      const [oRes, bRes] = await Promise.all([api.getQueue(), api.getBatchQueue()])
      setOrders(oRes.data  || [])
      setBatches(bRes.data || [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function flash(m) { setMsg(m); setTimeout(() => setMsg(''), 4000) }

  async function handleApprove(token) {
    setActing(token); setError('')
    try {
      await api.approveOrder(token)
      flash('Order approved — SAP submission running in background')
      setOrders(o => o.filter(x => x.token !== token))
    } catch (e) { setError(e.message) }
    finally { setActing(null) }
  }

  async function handleReject(token) {
    if (!window.confirm('Reject this order?')) return
    setActing(token); setError('')
    try {
      await api.rejectOrder(token)
      flash('Order rejected')
      setOrders(o => o.filter(x => x.token !== token))
    } catch (e) { setError(e.message) }
    finally { setActing(null) }
  }

  async function handleBatchApprove(token, batchId) {
    if (!window.confirm(`Approve all orders in batch ${batchId}?`)) return
    setActing(token); setError('')
    try {
      await api.approveBatch(token)
      flash(`Batch ${batchId} approved — SAP submission running in background`)
      setBatches(b => b.filter(x => x.token !== token))
    } catch (e) { setError(e.message) }
    finally { setActing(null) }
  }

  async function handleBatchReject(token, batchId) {
    if (!window.confirm(`Reject all orders in batch ${batchId}?`)) return
    setActing(token); setError('')
    try {
      await api.rejectBatch(token)
      flash(`Batch ${batchId} rejected`)
      setBatches(b => b.filter(x => x.token !== token))
    } catch (e) { setError(e.message) }
    finally { setActing(null) }
  }

  const totalOrderValue = orders.reduce((s, o) => s + o.value, 0)
  const totalBatchValue = batches.reduce((s, b) => s + b.total_value, 0)
  const totalPending    = orders.length + batches.length

  return (
    <div className="page-body">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>Approval Queue</h1>
        <button className="btn-clear" onClick={loadAll}>&#8635; Refresh</button>
      </div>

      {msg   && <div className="msg-success">{msg}</div>}
      {error && <div className="msg-error">{error}</div>}

      {!loading && totalPending > 0 && (
        <div className="stats-row" style={{ gridTemplateColumns: 'repeat(3,1fr)', marginBottom: 20 }}>
          <div className="stat-card pending">
            <div className="stat-label">Pending Items</div>
            <div className="stat-number">{totalPending}</div>
            <div className="stat-hint">{orders.length} orders · {batches.length} batches</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Orders Value</div>
            <div className="stat-number" style={{ fontSize: 20 }}>{fmtINR(totalOrderValue)}</div>
            <div className="stat-hint">{orders.length} individual orders</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Batches Value</div>
            <div className="stat-number" style={{ fontSize: 20 }}>{fmtINR(totalBatchValue)}</div>
            <div className="stat-hint">{batches.length} batch orders</div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading">Loading…</div>
      ) : (
        <>
          {/* ── Individual Orders ── */}
          <div className="card" style={{ marginBottom: 20 }}>
            <div className="card-header">
              Individual Orders
              <span className="card-header-sub">{orders.length} pending</span>
            </div>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th><th>Employee</th><th>Plant</th><th>Part No</th>
                    <th>Qty</th><th>Unit Price</th><th>Value</th><th>Date</th><th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.length === 0 && (
                    <tr><td colSpan={9} className="empty">No pending orders — all clear!</td></tr>
                  )}
                  {orders.map(o => (
                    <tr key={o.token}>
                      <td>{o.id}</td>
                      <td><strong>{o.employee_id}</strong></td>
                      <td>{o.plant}</td>
                      <td>{o.part_no}</td>
                      <td>{o.quantity}</td>
                      <td>{fmtINR(o.unit_price)}</td>
                      <td><strong style={{ color: '#1a3c5e' }}>{fmtINR(o.value)}</strong></td>
                      <td>{o.created_at}</td>
                      <td>
                        <div style={{ display: 'flex', gap: 6 }}>
                          <button className="btn-action-sm btn-action-green"
                            disabled={acting === o.token}
                            onClick={() => handleApprove(o.token)}>
                            {acting === o.token ? '…' : 'Approve'}
                          </button>
                          <button className="btn-action-sm btn-action-red"
                            disabled={acting === o.token}
                            onClick={() => handleReject(o.token)}>
                            {acting === o.token ? '…' : 'Reject'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* ── Batch Orders ── */}
          <div className="card">
            <div className="card-header">
              Batch Orders
              <span className="card-header-sub">{batches.length} pending</span>
            </div>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Batch ID</th><th>Employee</th><th>Orders</th>
                    <th>Total Value</th><th>Date</th><th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {batches.length === 0 && (
                    <tr><td colSpan={6} className="empty">No pending batches — all clear!</td></tr>
                  )}
                  {batches.map(b => (
                    <tr key={b.token}>
                      <td><strong style={{ fontFamily: 'monospace' }}>{b.batch_id}</strong></td>
                      <td><strong>{b.employee_id}</strong></td>
                      <td>
                        <span style={{ background: '#e0f2fe', color: '#0369a1', borderRadius: 10,
                          padding: '2px 8px', fontSize: 12, fontWeight: 600 }}>
                          {b.order_count} orders
                        </span>
                      </td>
                      <td><strong style={{ color: '#1a3c5e' }}>{fmtINR(b.total_value)}</strong></td>
                      <td>{b.created_at}</td>
                      <td>
                        <div style={{ display: 'flex', gap: 6 }}>
                          <button className="btn-action-sm btn-action-green"
                            disabled={acting === b.token}
                            onClick={() => handleBatchApprove(b.token, b.batch_id)}>
                            {acting === b.token ? '…' : `Approve All`}
                          </button>
                          <button className="btn-action-sm btn-action-red"
                            disabled={acting === b.token}
                            onClick={() => handleBatchReject(b.token, b.batch_id)}>
                            {acting === b.token ? '…' : 'Reject All'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
