let _onUnauthorized = null

export function setUnauthorizedHandler(fn) {
  _onUnauthorized = fn
}

function getToken() {
  return localStorage.getItem('bm_token')
}

async function request(method, path, body = null) {
  const headers = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  const data = await res.json()
  if (!res.ok) {
    if (res.status === 401) {
      _onUnauthorized?.()
      throw new Error('Your session has expired. Please log in again.')
    }
    throw new Error(data.message || data.detail || `Request failed (${res.status})`)
  }
  return data
}

export const api = {
  // Auth
  login: (employee_id, password) =>
    request('POST', '/login', { employee_id, password }),

  // Operator — orders
  createOrder: (plant, part_no, quantity, remark) =>
    request('POST', '/orders', { plant, part_no, quantity, remark: remark || null }),
  getOrders: () =>
    request('GET', '/orders/me'),
  getPartsForPlant: (plant) =>
    request('GET', `/products/parts?plant=${encodeURIComponent(plant)}`),

  // Operator — batches
  createBatch: (items, remark) =>
    request('POST', '/batches', { items, remark: remark || null }),
  getBatches: () =>
    request('GET', '/batches/me'),

  // Approval (email-link endpoints, no auth required)
  approveOrder: (token) =>
    request('GET', `/approve/${token}`),
  rejectOrder: (token) =>
    request('GET', `/reject/${token}`),
  approveBatch: (token) =>
    request('GET', `/approve/batch/${token}`),
  rejectBatch: (token) =>
    request('GET', `/reject/batch/${token}`),

  // Manager — individual orders
  getQueue: () =>
    request('GET', '/management/queue'),
  getApprovalHistory: (status = null) =>
    request('GET', `/management/history${status ? `?status=${status}` : ''}`),
  reApproveOrder: (token) =>
    request('POST', `/management/orders/${token}/re-approve`),

  // Manager — batch orders
  getBatchQueue: () =>
    request('GET', '/management/batches/queue'),

  // Admin — users
  getUsers: (includeInactive = false) =>
    request('GET', `/admin/users${includeInactive ? '?include_inactive=true' : ''}`),
  createUser: (data) =>
    request('POST', '/admin/users', data),
  updateUser: (employeeId, data) =>
    request('PUT', `/admin/users/${employeeId}`, data),
  resetPassword: (employeeId, newPassword) =>
    request('POST', `/admin/users/${employeeId}/reset-password`, { new_password: newPassword }),
  deactivateUser: (employeeId) =>
    request('DELETE', `/admin/users/${employeeId}`),

  // Admin — products upload (multipart)
  uploadProducts: async (file) => {
    const form = new FormData()
    form.append('file', file)
    const token = getToken()
    const res = await fetch('/admin/products/upload', {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.message || data.detail || `Upload failed (${res.status})`)
    return data
  },

  // Admin — audit logs
  getAuditLogs: (params = {}) => {
    const q = new URLSearchParams(params).toString()
    return request('GET', `/admin/audit-logs${q ? `?${q}` : ''}`)
  },
}
