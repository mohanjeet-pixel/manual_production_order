import { useState, useEffect } from 'react'
import { setUnauthorizedHandler } from './api.js'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import NewOrder from './pages/NewOrder.jsx'
import BatchOrder from './pages/BatchOrder.jsx'
import History from './pages/History.jsx'
import AdminUsers from './pages/admin/AdminUsers.jsx'
import AdminProducts from './pages/admin/AdminProducts.jsx'
import ManagerQueue from './pages/manager/ManagerQueue.jsx'
import ManagerHistory from './pages/manager/ManagerHistory.jsx'
import Layout from './components/Layout.jsx'

const DEFAULT_PAGE = {
  OPERATOR: 'dashboard',
  MANAGER:  'queue',
  ADMIN:    'users',
}

export default function App() {
  const [user, setUser] = useState(null)
  const [page, setPage] = useState('dashboard')

  useEffect(() => {
    const saved = localStorage.getItem('bm_user')
    if (saved) {
      try {
        const u = JSON.parse(saved)
        setUser(u)
        setPage(DEFAULT_PAGE[u.role] || 'dashboard')
      } catch { /* ignore */ }
    }
  }, [])

  function handleLogin(userData) {
    localStorage.setItem('bm_token', userData.token)
    localStorage.setItem('bm_user', JSON.stringify(userData))
    setUser(userData)
    setPage(DEFAULT_PAGE[userData.role] || 'dashboard')
  }

  function handleLogout() {
    localStorage.removeItem('bm_token')
    localStorage.removeItem('bm_user')
    setUser(null)
    setPage('dashboard')
  }

  useEffect(() => {
    setUnauthorizedHandler(handleLogout)
  }, [])

  if (!user) return <Login onLogin={handleLogin} />

  const pages = {
    // Operator
    dashboard:  <Dashboard />,
    'new-order': <NewOrder />,
    batch:       <BatchOrder />,
    history:     <History />,
    // Manager
    queue:          <ManagerQueue />,
    'mgmt-history': <ManagerHistory />,
    // Admin
    users:    <AdminUsers />,
    products: <AdminProducts />,
  }

  return (
    <Layout user={user} page={page} onNavigate={setPage} onLogout={handleLogout}>
      {pages[page] || <div className="loading">Page not found</div>}
    </Layout>
  )
}
