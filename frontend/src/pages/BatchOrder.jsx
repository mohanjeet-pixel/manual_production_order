import { useState, useEffect, useRef } from 'react'
import { api } from '../api.js'
import StatusBadge from '../components/StatusBadge.jsx'
import { fmtINR } from '../utils.js'

const emptyRow = () => ({ part_no: '', quantity: '', price: null })

function SapTag({ status }) {
  if (!status) return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4,
      fontSize: 11, color: '#92400e', background: '#fef3c7',
      border: '1px solid #fcd34d', borderRadius: 10, padding: '1px 7px' }}>
      <span className="sap-spinner" style={{ width: 8, height: 8 }} /> SAP
    </span>
  )
  if (status === 'SUCCESS') return (
    <span style={{ fontSize: 11, color: '#15803d', background: '#dcfce7',
      border: '1px solid #86efac', borderRadius: 10, padding: '1px 7px' }}>✓ SAP</span>
  )
  return (
    <span style={{ fontSize: 11, color: '#b91c1c', background: '#fee2e2',
      border: '1px solid #fca5a5', borderRadius: 10, padding: '1px 7px' }}>✗ SAP</span>
  )
}

export default function BatchOrder() {
  const [tab, setTab]           = useState('new')

  // ── New Batch ──────────────────────────────────────────────
  const [plant, setPlant]       = useState('')
  const [parts, setParts]       = useState([])
  const [partsMap, setPartsMap] = useState({})
  const [partsLoading, setPartsLoading] = useState(false)
  const [rows, setRows]         = useState([emptyRow(), emptyRow(), emptyRow()])
  const [msg, setMsg]           = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const plantTimer              = useRef(null)

  // ── History ────────────────────────────────────────────────
  const [batches, setBatches]   = useState([])
  const [histLoading, setHistLoading] = useState(false)
  const [expanded, setExpanded] = useState({})

  // Load parts when plant changes
  useEffect(() => {
    setRows(prev => prev.map(r => ({ ...r, part_no: '', price: null })))
    setParts([]); setPartsMap({})
    if (!plant.trim()) return
    clearTimeout(plantTimer.current)
    plantTimer.current = setTimeout(() => {
      setPartsLoading(true)
      api.getPartsForPlant(plant.trim())
        .then(res => {
          const list = res.data || []
          setParts(list)
          const map = {}
          list.forEach(p => { map[p.part_no] = p.price })
          setPartsMap(map)
        })
        .catch(() => { setParts([]); setPartsMap({}) })
        .finally(() => setPartsLoading(false))
    }, 600)
    return () => clearTimeout(plantTimer.current)
  }, [plant])

  // Load history when tab switches to history
  useEffect(() => {
    if (tab !== 'history') return
    setHistLoading(true)
    api.getBatches()
      .then(res => setBatches(Array.isArray(res) ? res : (res.data || [])))
      .catch(() => {})
      .finally(() => setHistLoading(false))
  }, [tab])

  function updateRow(i, field, val) {
    setRows(prev => prev.map((r, idx) => {
      if (idx !== i) return r
      const updated = { ...r, [field]: val }
      if (field === 'part_no') updated.price = partsMap[val.trim()] ?? null
      return updated
    }))
  }

  function addRow()     { setRows(prev => [...prev, emptyRow()]) }
  function removeRow(i) { if (rows.length > 1) setRows(prev => prev.filter((_, idx) => idx !== i)) }

  const filledRows = rows.filter(r => r.part_no.trim() && r.quantity && r.price !== null)
  const totalValue = filledRows.reduce((s, r) => s + r.price * parseFloat(r.quantity), 0)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!plant.trim()) { setMsg({ type: 'error', text: 'Enter a plant code first.' }); return }
    if (!filledRows.length) { setMsg({ type: 'error', text: 'Add at least one complete row.' }); return }
    setSubmitting(true); setMsg(null)
    try {
      const items = filledRows.map(r => ({
        plant: plant.trim(), part_no: r.part_no.trim(), quantity: parseFloat(r.quantity),
      }))
      const res = await api.createBatch(items)
      setMsg({ type: 'success', text: res.message || 'Batch created successfully' })
      setPlant(''); setRows([emptyRow(), emptyRow(), emptyRow()])
      setParts([]); setPartsMap({})
    } catch (err) {
      setMsg({ type: 'error', text: err.message })
    } finally {
      setSubmitting(false)
    }
  }

  function handleClear() {
    setPlant(''); setRows([emptyRow(), emptyRow(), emptyRow()])
    setParts([]); setPartsMap({}); setMsg(null)
  }

  function toggleExpand(bid) {
    setExpanded(e => ({ ...e, [bid]: !e[bid] }))
  }

  return (
    <div className="page-body">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div className="page-title" style={{ marginBottom: 0 }}>Batch Production Order</div>
        <div className="filter-tabs">
          <button className={`filter-btn${tab === 'new' ? ' active' : ''}`} onClick={() => setTab('new')}>
            New Batch
          </button>
          <button className={`filter-btn${tab === 'history' ? ' active' : ''}`} onClick={() => setTab('history')}>
            History
          </button>
        </div>
      </div>

      {/* ═══ NEW BATCH TAB ═══════════════════════════════════ */}
      {tab === 'new' && (
        <div className="card">
          <div className="card-header">Order Items</div>
          <div className="card-body">
            <form onSubmit={handleSubmit}>

              {/* Plant + total value */}
              <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start', marginBottom: 20, flexWrap: 'wrap' }}>
                <div style={{ flex: '0 0 220px' }}>
                  <label className="field-label">Plant (all rows)</label>
                  <input
                    className="field-input"
                    placeholder="e.g. 1500"
                    value={plant}
                    onChange={e => setPlant(e.target.value)}
                  />
                  {partsLoading && <span className="field-hint">Loading parts…</span>}
                  {!partsLoading && plant && parts.length > 0 &&
                    <span className="field-hint">{parts.length} parts available</span>}
                  {!partsLoading && plant && parts.length === 0 &&
                    <span className="field-hint-error">No parts found for this plant</span>}
                </div>

                {totalValue > 0 && (
                  <div style={{ flex: 1, minWidth: 200, background: '#f0fdf4',
                    border: '1px solid #bbf7d0', borderRadius: 8, padding: '10px 16px' }}>
                    <div style={{ fontSize: 11, color: '#15803d', fontWeight: 600, marginBottom: 2 }}>
                      TOTAL BATCH VALUE
                    </div>
                    <div style={{ fontSize: 24, fontWeight: 700, color: '#15803d' }}>
                      {fmtINR(totalValue)}
                    </div>
                    <div style={{ fontSize: 11, color: '#16a34a' }}>
                      {filledRows.length} line{filledRows.length !== 1 ? 's' : ''}
                    </div>
                  </div>
                )}
              </div>

              {/* Row header */}
              <div className="batch-header-row" style={{ gridTemplateColumns: '28px 2fr 1fr 1fr 1fr 32px' }}>
                <div className="batch-col-label">#</div>
                <div className="batch-col-label">Part Number</div>
                <div className="batch-col-label">Quantity</div>
                <div className="batch-col-label">Unit Price</div>
                <div className="batch-col-label">Line Value</div>
                <div />
              </div>

              {/* Rows */}
              {rows.map((row, i) => {
                const lineVal = row.price !== null && row.quantity
                  ? row.price * parseFloat(row.quantity) : null
                const partDesc = parts.find(p => p.part_no === row.part_no.trim())?.description
                return (
                  <div key={i}>
                    <div className="batch-row" style={{ gridTemplateColumns: '28px 2fr 1fr 1fr 1fr 32px' }}>
                      <div className="batch-row-num">{i + 1}</div>
                      <div>
                        <input
                          className="field-input"
                          list={`pl-${i}`}
                          placeholder={parts.length ? 'Type to search part…' : 'Enter plant first'}
                          value={row.part_no}
                          onChange={e => updateRow(i, 'part_no', e.target.value)}
                          disabled={parts.length === 0}
                          autoComplete="off"
                        />
                        <datalist id={`pl-${i}`}>
                          {parts.map(p => (
                            <option key={p.part_no} value={p.part_no}>{p.description}</option>
                          ))}
                        </datalist>
                        {partDesc && <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{partDesc}</div>}
                      </div>
                      <input
                        className="field-input"
                        type="number" min="1" step="any"
                        placeholder="Qty"
                        value={row.quantity}
                        onChange={e => updateRow(i, 'quantity', e.target.value)}
                      />
                      <div className="field-display" style={{ height: 36 }}>
                        {row.price !== null ? fmtINR(row.price) : '—'}
                      </div>
                      <div className="field-display" style={{ height: 36,
                        color: lineVal ? '#1a3c5e' : undefined,
                        fontWeight: lineVal ? 700 : undefined }}>
                        {lineVal !== null ? fmtINR(lineVal) : '—'}
                      </div>
                      <button type="button" className="btn-row-remove"
                        onClick={() => removeRow(i)} disabled={rows.length <= 1}>×</button>
                    </div>
                  </div>
                )
              })}

              <button type="button" className="btn-add-row" onClick={addRow}>+ Add Row</button>

              {msg && <div className={`msg-${msg.type}`} style={{ marginTop: 14 }}>{msg.text}</div>}

              <div className="form-actions" style={{ marginTop: 18 }}>
                <button type="submit" className="btn-submit"
                  disabled={submitting || !filledRows.length || !plant.trim()}>
                  {submitting ? 'Submitting…' : `Submit Batch (${filledRows.length} item${filledRows.length !== 1 ? 's' : ''}) →`}
                </button>
                <button type="button" className="btn-clear" onClick={handleClear}>Clear</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ═══ HISTORY TAB ═════════════════════════════════════ */}
      {tab === 'history' && (
        <div className="card">
          <div className="card-header">
            Batch History
            <span className="card-header-sub">{batches.length} batches</span>
          </div>
          {histLoading ? (
            <div className="loading">Loading…</div>
          ) : batches.length === 0 ? (
            <div className="empty" style={{ padding: 40 }}>No batch orders yet</div>
          ) : (
            <div style={{ padding: '8px 16px 16px' }}>
              {batches.map(b => (
                <div key={b['Batch ID']} className="batch-history-item">
                  <div
                    className="batch-history-header"
                    onClick={() => toggleExpand(b['Batch ID'])}
                    style={{ cursor: 'pointer' }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ fontSize: 11, color: '#94a3b8', transition: 'transform 0.2s',
                        display: 'inline-block',
                        transform: expanded[b['Batch ID']] ? 'rotate(90deg)' : 'rotate(0deg)' }}>▶</span>
                      <strong style={{ fontFamily: 'monospace', fontSize: 13 }}>{b['Batch ID']}</strong>
                      <StatusBadge status={b.Status} />
                    </div>
                    <div style={{ display: 'flex', gap: 20, alignItems: 'center', fontSize: 13 }}>
                      <span style={{ color: '#64748b' }}>{b.Orders?.length || 0} orders</span>
                      <strong style={{ color: '#1a3c5e' }}>{fmtINR(b['Total Value'])}</strong>
                      <span style={{ color: '#94a3b8', fontSize: 12 }}>{b['Created At']}</span>
                    </div>
                  </div>

                  {expanded[b['Batch ID']] && (
                    <div className="batch-history-orders">
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>Plant</th><th>Part No</th><th>Qty</th>
                            <th>Unit Price</th><th>Value</th><th>SAP</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(b.Orders || []).map(o => (
                            <tr key={o.ID}>
                              <td>{o.Plant}</td>
                              <td>{o['Part No']}</td>
                              <td>{o.Quantity}</td>
                              <td>{fmtINR(o['Unit Price'])}</td>
                              <td><strong>{fmtINR(o.Value)}</strong></td>
                              <td>
                                {b.Status === 'APPROVED'
                                  ? <SapTag status={o.sap_status} />
                                  : <span style={{ color: '#94a3b8' }}>—</span>}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {b.Status === 'APPROVED' && b.Orders?.some(o => !o.sap_status) && (
                        <div style={{ fontSize: 11, color: '#92400e', padding: '6px 12px',
                          background: '#fef3c7', borderTop: '1px solid #fde68a' }}>
                          SAP submissions are running in background — refresh to update
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
