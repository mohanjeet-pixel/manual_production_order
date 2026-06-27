import { useState, useEffect } from 'react'
import { api } from '../api.js'
import { fmtINR } from '../utils.js'

export default function NewOrder() {
  const [plant, setPlant]       = useState('')
  const [partNo, setPartNo]     = useState('')
  const [price, setPrice]       = useState(null)
  const [priceErr, setPriceErr] = useState(false)
  const [quantity, setQuantity] = useState('')
  const [msg, setMsg]           = useState(null)
  const [loading, setLoading]   = useState(false)

  useEffect(() => {
    if (!partNo.trim()) { setPrice(null); setPriceErr(false); return }
    const timer = setTimeout(() => {
      api.getPartPrice(partNo.trim())
        .then(data => { setPrice(data.price); setPriceErr(false) })
        .catch(() => { setPrice(null); setPriceErr(true) })
    }, 500)
    return () => clearTimeout(timer)
  }, [partNo])

  const value = price && quantity ? parseFloat(quantity) * price : null

  async function handleSubmit(e) {
    e.preventDefault()
    if (!plant.trim() || !partNo.trim() || !quantity) {
      setMsg({ type: 'error', text: 'Please fill all fields.' }); return
    }
    if (!price) {
      setMsg({ type: 'error', text: 'Part number not found or price unavailable.' }); return
    }
    setLoading(true); setMsg(null)
    try {
      const res = await api.createOrder(plant.trim(), partNo.trim(), parseFloat(quantity))
      setMsg({ type: 'success', text: res.message })
      setPlant(''); setPartNo(''); setQuantity(''); setPrice(null); setPriceErr(false)
    } catch (err) {
      setMsg({ type: 'error', text: err.message })
    } finally {
      setLoading(false)
    }
  }

  function handleClear() {
    setPlant(''); setPartNo(''); setQuantity(''); setPrice(null); setPriceErr(false); setMsg(null)
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
                <input className="field-input" placeholder="e.g. P01" value={plant}
                  onChange={e => setPlant(e.target.value)} />
              </div>

              <div className="form-field">
                <label className="field-label">Part Number</label>
                <input className="field-input" placeholder="e.g. BM-1234" value={partNo}
                  onChange={e => setPartNo(e.target.value)} />
                {priceErr && <span className="field-hint-error">Part not found</span>}
              </div>

              <div className="form-field">
                <label className="field-label">Unit Price (auto)</label>
                <div className="field-display">
                  {price !== null ? fmtINR(price) : '—'}
                </div>
              </div>

              <div className="form-field">
                <label className="field-label">Quantity</label>
                <input className="field-input" type="number" min="1" placeholder="0"
                  value={quantity} onChange={e => setQuantity(e.target.value)} />
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
              <button type="submit" className="btn-submit" disabled={loading}>
                {loading ? 'Submitting...' : 'Submit Order →'}
              </button>
              <button type="button" className="btn-clear" onClick={handleClear}>Clear</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
