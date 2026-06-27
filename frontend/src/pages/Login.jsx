import { useState } from 'react'
import { api } from '../api.js'

export default function Login({ onLogin }) {
  const [empId, setEmpId] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!empId.trim() || !password) {
      setError('Please enter Employee ID and Password.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await api.login(empId.trim(), password)
      if (res.success) {
        onLogin(res)
      } else {
        setError(res.message || 'Login failed.')
      }
    } catch (err) {
      setError(err.message || 'Login failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-brand">
          <span className="login-icon">&#127981;</span>
          <div className="login-brand-title">Bull Machines</div>
          <div className="login-brand-sub">Manual Production Orders</div>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Employee ID</label>
            <input
              type="text"
              className="form-input"
              placeholder="Enter Employee ID"
              value={empId}
              onChange={e => setEmpId(e.target.value)}
              autoFocus
            />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              className="form-input"
              placeholder="Enter Password"
              value={password}
              onChange={e => setPassword(e.target.value)}
            />
          </div>
          {error && <div className="msg-error">{error}</div>}
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Logging in...' : 'Login →'}
          </button>
        </form>
      </div>
    </div>
  )
}
