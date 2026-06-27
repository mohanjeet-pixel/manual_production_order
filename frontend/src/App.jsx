import { useState, useEffect } from 'react'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import NewOrder from './pages/NewOrder.jsx'
import BatchOrder from './pages/BatchOrder.jsx'
import History from './pages/History.jsx'
import Layout from './components/Layout.jsx'

export default function App() {
  const [user, setUser] = useState(null)
  const [page, setPage] = useState('dashboard')

  useEffect(() => {
    const saved = localStorage.getItem('bm_user')
    if (saved) {
      try { setUser(JSON.parse(saved)) } catch { /* ignore */ }
    }
  }, [])

  function handleLogin(userData) {
    localStorage.setItem('bm_token', userData.token)
    localStorage.setItem('bm_user', JSON.stringify(userData))
    setUser(userData)
  }

  function handleLogout() {
    localStorage.removeItem('bm_token')
    localStorage.removeItem('bm_user')
    setUser(null)
    setPage('dashboard')
  }

  if (!user) return <Login onLogin={handleLogin} />

  const pages = {
    dashboard: <Dashboard />,
    'new-order': <NewOrder />,
    batch: <BatchOrder />,
    history: <History />,
  }

  return (
    <Layout user={user} page={page} onNavigate={setPage} onLogout={handleLogout}>
      {pages[page]}
    </Layout>
  )
}
