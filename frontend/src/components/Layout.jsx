const TABS = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'new-order', label: 'New Order' },
  { id: 'batch',     label: 'Batch Order' },
  { id: 'history',   label: 'History' },
]

export default function Layout({ user, page, onNavigate, onLogout, children }) {
  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <span className="header-logo">&#127981;</span>
          <span className="header-title">Bull Machines</span>
          <span className="header-divider">|</span>
          <span className="header-subtitle">Manual Production Orders</span>
        </div>
        <div className="header-right">
          <span className="header-user">&#128100; {user.employee_id}</span>
          <button className="btn-logout" onClick={onLogout}>Logout</button>
        </div>
      </header>

      <nav className="app-nav">
        {TABS.map(tab => (
          <button
            key={tab.id}
            className={`nav-tab${page === tab.id ? ' active' : ''}`}
            onClick={() => onNavigate(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="app-main">
        {children}
      </main>
    </div>
  )
}
