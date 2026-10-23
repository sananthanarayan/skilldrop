import { lazy, Suspense, useState } from 'react'
import Users from './pages/Users'
import Orders from './pages/Orders'

type Tab = 'users' | 'orders' | 'analytics'

const Analytics = lazy(() => import('./pages/Analytics'))

export default function App() {
  const [tab, setTab] = useState<Tab>('users')
  return (
    <div>
      <nav>
        <button onClick={() => setTab('users')}>Users</button>
        <button onClick={() => setTab('orders')}>Orders</button>
        <button onClick={() => setTab('analytics')}>Analytics</button>
      </nav>
      {tab === 'users' && <Users />}
      {tab === 'orders' && <Orders />}
      {tab === 'analytics' && (
        <Suspense fallback={<p>Loading…</p>}>
          <Analytics />
        </Suspense>
      )}
    </div>
  )
}
