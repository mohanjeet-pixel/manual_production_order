import { useState, useEffect, Fragment } from 'react'
import { api } from '../../api.js'

const ROLE_STYLE = {
  ADMIN:    { background: '#fce7f3', color: '#9d174d' },
  MANAGER:  { background: '#ede9fe', color: '#5b21b6' },
  OPERATOR: { background: '#e0f2fe', color: '#075985' },
}

const EMPTY_FORM = {
  employee_id: '', full_name: '', email: '',
  department: '', role: 'OPERATOR', password: '',
}

export default function AdminUsers() {
  const [users, setUsers]               = useState([])
  const [loading, setLoading]           = useState(true)
  const [includeInactive, setIncludeInactive] = useState(false)
  const [showAdd, setShowAdd]           = useState(false)
  const [addForm, setAddForm]           = useState(EMPTY_FORM)
  const [resetRow, setResetRow]         = useState(null)
  const [resetPw, setResetPw]           = useState('')
  const [msg, setMsg]                   = useState('')
  const [error, setError]               = useState('')

  useEffect(() => { loadUsers() }, [includeInactive])

  async function loadUsers() {
    setLoading(true)
    setError('')
    try {
      const res = await api.getUsers(includeInactive)
      setUsers(res.data || [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function flash(m) { setMsg(m); setTimeout(() => setMsg(''), 3500) }

  async function handleAddUser(e) {
    e.preventDefault()
    setError('')
    try {
      await api.createUser(addForm)
      flash(`User ${addForm.employee_id} created successfully`)
      setShowAdd(false)
      setAddForm(EMPTY_FORM)
      loadUsers()
    } catch (e) { setError(e.message) }
  }

  async function handleResetPassword(employeeId) {
    if (!resetPw.trim()) return
    setError('')
    try {
      await api.resetPassword(employeeId, resetPw)
      flash(`Password reset for ${employeeId}`)
      setResetRow(null)
      setResetPw('')
    } catch (e) { setError(e.message) }
  }

  async function handleDeactivate(employeeId) {
    if (!window.confirm(`Deactivate ${employeeId}? They will no longer be able to log in.`)) return
    setError('')
    try {
      await api.deactivateUser(employeeId)
      flash(`${employeeId} deactivated`)
      loadUsers()
    } catch (e) { setError(e.message) }
  }

  function toggleReset(employeeId) {
    if (resetRow === employeeId) { setResetRow(null); setResetPw('') }
    else { setResetRow(employeeId); setResetPw('') }
  }

  return (
    <div className="page-body">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>User Management</h1>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <label style={{ fontSize: 13, color: '#64748b', display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
            <input type="checkbox" checked={includeInactive} onChange={e => setIncludeInactive(e.target.checked)} />
            Show inactive
          </label>
          <button className="btn-submit" onClick={() => { setShowAdd(s => !s); setError('') }}>
            {showAdd ? 'Cancel' : '+ Add User'}
          </button>
        </div>
      </div>

      {msg   && <div className="msg-success">{msg}</div>}
      {error && <div className="msg-error">{error}</div>}

      {showAdd && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-header">Add New User</div>
          <div className="card-body">
            <form onSubmit={handleAddUser}>
              <div className="order-grid">
                <div>
                  <label className="field-label">Employee ID *</label>
                  <input className="field-input" required
                    value={addForm.employee_id}
                    onChange={e => setAddForm(f => ({ ...f, employee_id: e.target.value.toUpperCase() }))}
                    placeholder="EMP006" />
                </div>
                <div>
                  <label className="field-label">Full Name *</label>
                  <input className="field-input" required
                    value={addForm.full_name}
                    onChange={e => setAddForm(f => ({ ...f, full_name: e.target.value }))}
                    placeholder="John Doe" />
                </div>
                <div>
                  <label className="field-label">Email *</label>
                  <input className="field-input" type="email" required
                    value={addForm.email}
                    onChange={e => setAddForm(f => ({ ...f, email: e.target.value }))}
                    placeholder="john@bullmachines.com" />
                </div>
                <div>
                  <label className="field-label">Department</label>
                  <input className="field-input"
                    value={addForm.department}
                    onChange={e => setAddForm(f => ({ ...f, department: e.target.value }))}
                    placeholder="Production" />
                </div>
                <div>
                  <label className="field-label">Role *</label>
                  <select className="field-input" value={addForm.role}
                    onChange={e => setAddForm(f => ({ ...f, role: e.target.value }))}>
                    <option value="OPERATOR">OPERATOR — Create orders</option>
                    <option value="MANAGER">MANAGER — Approve orders</option>
                    <option value="ADMIN">ADMIN — Full access</option>
                  </select>
                </div>
                <div>
                  <label className="field-label">Password *</label>
                  <input className="field-input" type="password" required
                    value={addForm.password}
                    onChange={e => setAddForm(f => ({ ...f, password: e.target.value }))}
                    placeholder="Min 4 characters" />
                </div>
              </div>
              <div className="form-actions">
                <button type="submit" className="btn-submit">Create User</button>
                <button type="button" className="btn-clear" onClick={() => { setShowAdd(false); setAddForm(EMPTY_FORM) }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-header">
          All Users
          <span className="card-header-sub">{users.length} records</span>
        </div>
        {loading ? (
          <div className="loading">Loading...</div>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Employee ID</th>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Department</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.length === 0 && (
                  <tr><td colSpan={7} className="empty">No users found</td></tr>
                )}
                {users.map(u => (
                  <Fragment key={u.employee_id}>
                    <tr>
                      <td><strong>{u.employee_id}</strong></td>
                      <td>{u.full_name || '—'}</td>
                      <td style={{ color: '#475569' }}>{u.email || '—'}</td>
                      <td>{u.department || '—'}</td>
                      <td>
                        <span className="badge" style={ROLE_STYLE[u.role] || { background: '#f1f5f9', color: '#475569' }}>
                          {u.role}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${u.is_active ? 'badge-approved' : 'badge-rejected'}`}>
                          {u.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: 8 }}>
                          <button className="btn-action-sm btn-action-blue" onClick={() => toggleReset(u.employee_id)}>
                            {resetRow === u.employee_id ? 'Cancel' : 'Reset PW'}
                          </button>
                          {u.is_active && (
                            <button className="btn-action-sm btn-action-red" onClick={() => handleDeactivate(u.employee_id)}>
                              Deactivate
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                    {resetRow === u.employee_id && (
                      <tr style={{ background: '#f8fafc' }}>
                        <td colSpan={7} style={{ padding: '10px 14px' }}>
                          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                            <input
                              className="field-input"
                              type="password"
                              placeholder="Enter new password"
                              value={resetPw}
                              onChange={e => setResetPw(e.target.value)}
                              onKeyDown={e => e.key === 'Enter' && handleResetPassword(u.employee_id)}
                              style={{ maxWidth: 280 }}
                              autoFocus
                            />
                            <button className="btn-submit" onClick={() => handleResetPassword(u.employee_id)}>
                              Set Password
                            </button>
                            <button className="btn-clear" onClick={() => { setResetRow(null); setResetPw('') }}>
                              Cancel
                            </button>
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
