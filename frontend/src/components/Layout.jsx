const TABS = {
  OPERATOR: [
    { id: 'dashboard',  label: 'Dashboard' },
    { id: 'new-order',  label: 'New Order' },
    { id: 'batch',      label: 'Batch Order' },
    { id: 'history',    label: 'History' },
  ],
  MANAGER: [
    { id: 'queue',        label: 'Approval Queue' },
    { id: 'mgmt-history', label: 'History' },
  ],
  ADMIN: [
    { id: 'users',    label: 'Users' },
    { id: 'products', label: 'Products Upload' },
  ],
}

const ROLE_LABEL = { OPERATOR: 'Operator', MANAGER: 'Manager', ADMIN: 'Admin' }

export default function Layout({ user, page, onNavigate, onLogout, children }) {
  const tabs = TABS[user.role] || TABS.OPERATOR

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
          <span className="header-role-badge">{ROLE_LABEL[user.role] || user.role}</span>
          <span className="header-user">&#128100; {user.employee_id}</span>
          <button className="btn-logout" onClick={onLogout}>Logout</button>
        </div>
      </header>

      <nav className="app-nav">
        {tabs.map(tab => (
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
