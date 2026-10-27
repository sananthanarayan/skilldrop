import { lazy, Suspense } from 'react'
import Home from './pages/Home'
import Product from './pages/Product'

const Checkout = lazy(() => import('./pages/Checkout'))

export default function App() {
  const path = window.location.pathname
  if (path.startsWith('/checkout')) {
    return (
      <Suspense fallback={null}>
        <Checkout />
      </Suspense>
    )
  }
  if (path.startsWith('/p/')) return <Product />
  return <Home />
}
