import { lazy, Suspense } from 'react'
import Home from './pages/Home'

// Charts moved off the landing page in March (TPO-412) - Reports is lazy now.
const Reports = lazy(() => import('./pages/Reports'))

export const routes = [
  { path: '/', element: <Home /> },
  {
    path: '/reports',
    element: (
      <Suspense fallback={<p>Loading reports…</p>}>
        <Reports />
      </Suspense>
    ),
  },
]
