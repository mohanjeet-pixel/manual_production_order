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
    throw new Error(data.message || data.detail || `Request failed (${res.status})`)
  }
  return data
}

export const api = {
  login: (employee_id, password) =>
    request('POST', '/login', { employee_id, password }),

  createOrder: (plant, part_no, quantity) =>
    request('POST', '/orders', { plant, part_no, quantity }),

  getOrders: () =>
    request('GET', '/orders/me'),

  getPartPrice: (part_no) =>
    request('GET', `/products/price/${encodeURIComponent(part_no)}`),

  createBatch: (items) =>
    request('POST', '/batches', { items }),

  getBatches: () =>
    request('GET', '/batches/me'),
}
