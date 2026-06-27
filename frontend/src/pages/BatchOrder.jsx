import { useState } from 'react'
import { api } from '../api.js'

const emptyRow = () => ({ plant: '', part_no: '', quantity: '' })

export default function BatchOrder() {
  const [rows, setRows]       = useState([emptyRow(), emptyRow(), emptyRow()])
  const [msg, setMsg]         = useState(null)
  const [loading, setLoading] = useState(false)

  function updateRow(i, field, val) {
    setRows(prev => prev.map((r, idx) => idx === i ? { ...r, [field]: val } : r))
  }

  function addRow() {
    setRows(prev => [...prev, emptyRow()])
  }

  function removeRow(i) {
    if (rows.length <= 1) return
    setRows(prev => prev.filter((_, idx) => idx !== i))
  }

  const filledItems = rows.filter(r => r.plant.trim() && r.part_no.trim() && r.quantity)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!filledItems.length) {
      setMsg({ type: 'error', text: 'Please fill at least one complete row.' })
      return
    }
    setLoading(true)
    setMsg(null)
    try {
      const items = filledItems.map(r => ({
        plant:    r.plant.trim(),
        part_no:  r.part_no.trim(),
        quantity: parseFloat(r.quantity),
      }))
      const res = await api.createBatch(items)
      setMsg({ type: 'success', text: res.message || `Batch created successfully` })
      setRows([emptyRow(), emptyRow(), emptyRow()])
    } catch (err) {
      setMsg({ type: 'error', text: err.message || 'Failed to submit batch.' })
    } finally {
      setLoading(false)
    }
  }

  function handleClear() {
    setRows([emptyRow(), emptyRow(), emptyRow()])
    setMsg(null)
  }

  return (
    <div className="page-body">
      <div className="page-title">Batch Production Order</div>
      <div className="card">
        <div className="card-header">
          <span>Order Items</span>
          <span className="card-header-sub">{filledItems.length} of {rows.length} rows filled</span>
        </div>
        <div className="card-body">
          <form onSubmit={handleSubmit}>

            <div className="batch-header-row" style={{ gridTemplateColumns: '40px 1fr 1fr 1fr 36px' }}>
              <div className="batch-col-label" style={{ textAlign: 'center' }}>#</div>
              <div className="batch-col-label">Plant</div>
              <div className="batch-col-label">Part No</div>
              <div className="batch-col-label">Quantity</div>
              <div />
            </div>

            {rows.map((row, i) => (
              <div
                key={i}
                className="batch-row"
                style={{ gridTemplateColumns: '40px 1fr 1fr 1fr 36px' }}
              >
                <div className="batch-row-num">{i + 1}</div>
                <input
                  className="field-input"
                  placeholder="Plant"
                  value={row.plant}
                  onChange={e => updateRow(i, 'plant', e.target.value)}
                />
                <input
                  className="field-input"
                  placeholder="Part No"
                  value={row.part_no}
                  onChange={e => updateRow(i, 'part_no', e.target.value)}
                />
                <input
                  className="field-input"
                  type="number"
                  min="0.001"
                  step="any"
                  placeholder="Qty"
                  value={row.quantity}
                  onChange={e => updateRow(i, 'quantity', e.target.value)}
                />
                <button
                  type="button"
                  className="btn-row-remove"
                  onClick={() => removeRow(i)}
                  disabled={rows.length <= 1}
                  title="Remove row"
                >
                  ×
                </button>
              </div>
            ))}

            <button type="button" className="btn-add-row" onClick={addRow}>
              + Add Row
            </button>

            {msg && <div className={`msg-${msg.type}`}>{msg.text}</div>}

            <div className="form-actions" style={{ marginTop: 18 }}>
              <button
                type="submit"
                className="btn-submit"
                disabled={loading || !filledItems.length}
              >
                {loading ? 'Submitting…' : `Submit Batch (${filledItems.length} items) →`}
              </button>
              <button type="button" className="btn-clear" onClick={handleClear}>
                Clear
              </button>
            </div>

          </form>
        </div>
      </div>
    </div>
  )
}
