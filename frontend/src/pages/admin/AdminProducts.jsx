import { useState, useRef } from 'react'
import { api } from '../../api.js'

export default function AdminProducts() {
  const [file, setFile]       = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult]   = useState(null)
  const [error, setError]     = useState('')
  const inputRef              = useRef()

  function handleFileChange(e) {
    setFile(e.target.files[0] || null)
    setError('')
    setResult(null)
  }

  async function handleUpload() {
    if (!file) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await api.uploadProducts(file)
      setResult(res)
      setFile(null)
      if (inputRef.current) inputRef.current.value = ''
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function clearFile() {
    setFile(null)
    setError('')
    setResult(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div className="page-body">
      <h1 className="page-title">Products Upload</h1>

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">Upload Product Catalog</div>
        <div className="card-body">
          <p style={{ fontSize: 13, color: '#64748b', marginBottom: 16 }}>
            Upload a <strong>.csv</strong> or <strong>.xlsx</strong> file with these columns:
          </p>

          <div style={{
            background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8,
            padding: '12px 20px', marginBottom: 20, fontSize: 13, display: 'flex', gap: 24,
          }}>
            {['Material No', 'Description', 'Price', 'Plant'].map(col => (
              <span key={col} style={{ fontWeight: 600, color: '#1a3c5e', fontFamily: 'monospace' }}>{col}</span>
            ))}
          </div>

          <div
            className="upload-drop-zone"
            onClick={() => inputRef.current.click()}
          >
            <div style={{ fontSize: 36, marginBottom: 8 }}>&#128196;</div>
            <div style={{ fontWeight: 600, color: '#1a3c5e', marginBottom: 4 }}>
              {file ? file.name : 'Click to select file'}
            </div>
            <div style={{ fontSize: 12, color: '#94a3b8' }}>
              {file ? `${(file.size / 1024).toFixed(1)} KB` : 'Accepts .csv and .xlsx'}
            </div>
          </div>

          <input
            ref={inputRef}
            type="file"
            accept=".csv,.xlsx"
            style={{ display: 'none' }}
            onChange={handleFileChange}
          />

          {error  && <div className="msg-error">{error}</div>}
          {result && (
            <div className="msg-success">
              {result.message} &mdash; <strong>{result.data?.count}</strong> products loaded
            </div>
          )}

          <div className="form-actions">
            <button className="btn-submit" disabled={!file || loading} onClick={handleUpload}>
              {loading ? 'Uploading…' : 'Upload & Replace Catalog'}
            </button>
            {file && <button className="btn-clear" onClick={clearFile}>Clear</button>}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">Important Notes</div>
        <div className="card-body">
          <ul style={{ fontSize: 13, color: '#475569', lineHeight: 2.2, paddingLeft: 20 }}>
            <li>This upload <strong>fully replaces the product catalog</strong> — parts not in the file are removed.</li>
            <li>The <strong>Plant</strong> column must contain the plant code (e.g. <code>1000</code> or <code>1500</code>).</li>
            <li>Rows with a missing <strong>Material No</strong> or <strong>Price</strong> are skipped.</li>
            <li>Operators will only be able to order parts present in the uploaded catalog.</li>
            <li>Prices from this file are used to calculate order values and route to the correct approver.</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
