import { lazy, Suspense, useState } from 'react';
import BookingForm from './BookingForm';

const Reports = lazy(() => import(/* webpackChunkName: "admin" */ './admin/Reports'));

export default function App() {
  const [view, setView] = useState(window.location.hash === '#admin' ? 'admin' : 'book');
  return (
    <main>
      <nav>
        <button onClick={() => setView('book')}>Book</button>
        <button onClick={() => setView('admin')}>Staff reports</button>
      </nav>
      {view === 'book' ? (
        <BookingForm />
      ) : (
        <Suspense fallback={<p>Loading reports…</p>}>
          <Reports />
        </Suspense>
      )}
    </main>
  );
}
