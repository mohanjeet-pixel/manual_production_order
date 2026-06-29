import { useState, useEffect, useRef } from 'react'
import { api } from '../api.js'
import { fmtINR } from '../utils.js'

export default function NewOrder() {
  const [plant, setPlant]         = useState('')
  const [parts, setParts]         = useState([])
  const [partsMap, setPartsMap]   = useState({})
  const [partsLoading, setPartsLoading] = useState(false)
  const [partNo, setPartNo]       = useState('')
  const [price, setPrice]         = useState(null)
  const [quantity, setQuantity]   = useState('')
  const [msg, setMsg]             = useState(null)
  const [loading, setLoading]     = useState(false)
  const plantTimer                = useRef(null)

  useEffect(() => {
    setPartNo(''); setPrice(null); setParts([]); setPartsMap({})
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

  useEffect(() => {
    const p = partsMap[partNo.trim()]
    setPrice(p !== undefined ? p : null)
  }, [partNo, partsMap])

  const value = price !== null && quantity ? parseFloat(quantity) * price : null
  const partDescription = parts.find(p => p.part_no === partNo.trim())?.description

  async function handleSubmit(e) {
    e.preventDefault()
    if (!plant.trim() || !partNo.trim() || !quantity) {
      setMsg({ type: 'error', text: 'Please fill all fields.' }); return
    }
    if (price === null) {
      setMsg({ type: 'error', text: 'Select a valid part number from the list.' }); return
    }
    setLoading(true); setMsg(null)
    try {
      const res = await api.createOrder(plant.trim(), partNo.trim(), parseFloat(quantity))
      setMsg({ type: 'success', text: res.message })
      setPlant(''); setPartNo(''); setQuantity(''); setPrice(null)
      setParts([]); setPartsMap({})
    } catch (err) {
      setMsg({ type: 'error', text: err.message })
    } finally {
      setLoading(false)
    }
  }

  function handleClear() {
    setPlant(''); setPartNo(''); setQuantity(''); setPrice(null); setMsg(null)
    setParts([]); setPartsMap({})
  }

  return (
    <div className="page-body">
      <div className="page-title">New Production Order</div>
      <div className="card">
        <div className="card-header">Order Details</div>
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="order-grid">

              <div className="form-field">
                <label className="field-label">Plant</label>
                <input
                  className="field-input"
                  placeholder="e.g. 1500"
                  value={plant}
                  onChange={e => { setPlant(e.target.value) }}
                />
                {partsLoading && (
                  <span className="field-hint">Loading parts…</span>
                )}
                {!partsLoading && plant.trim() && parts.length > 0 && (
                  <span className="field-hint">{parts.length} parts available</span>
                )}
                {!partsLoading && plant.trim() && parts.length === 0 && (
                  <span className="field-hint-error">No parts found for this plant</span>
                )}
              </div>

              <div className="form-field">
                <label className="field-label">Part Number</label>
                <input
                  className="field-input"
                  list="parts-list"
                  placeholder={parts.length ? 'Type to search part…' : 'Enter plant first'}
                  value={partNo}
                  onChange={e => setPartNo(e.target.value)}
                  disabled={parts.length === 0}
                  autoComplete="off"
                />
                <datalist id="parts-list">
                  {parts.map(p => (
                    <option key={p.part_no} value={p.part_no}>{p.description}</option>
                  ))}
                </datalist>
                {partDescription && (
                  <span className="field-hint">{partDescription}</span>
                )}
              </div>

              <div className="form-field">
                <label className="field-label">Unit Price (auto)</label>
                <div className="field-display">
                  {price !== null ? fmtINR(price) : '—'}
                </div>
              </div>

              <div className="form-field">
                <label className="field-label">Quantity</label>
                <input
                  className="field-input"
                  type="number"
                  min="1"
                  placeholder="0"
                  value={quantity}
                  onChange={e => setQuantity(e.target.value)}
                />
              </div>

              <div className="form-field form-field-full">
                <label className="field-label">Estimated Value</label>
                <div className="field-display field-display-highlight">
                  {value !== null ? fmtINR(value) : '—'}
                </div>
              </div>

            </div>

            {msg && <div className={`msg-${msg.type}`}>{msg.text}</div>}

            <div className="form-actions">
              <button
                type="submit"
                className="btn-submit"
                disabled={loading || price === null || !quantity}
              >
                {loading ? 'Submitting…' : 'Submit Order →'}
              </button>
              <button type="button" className="btn-clear" onClick={handleClear}>Clear</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
